import io
import base64
import numpy as np
import os
import omero
from omero.gateway import BlitzGateway
from omero.model import enums as omero_enums
from omero.model import MapAnnotationI
from uuid import uuid4


PIXEL_TYPES = {
    omero_enums.PixelsTypeint8: np.int8,
    omero_enums.PixelsTypeuint8: np.uint8,
    omero_enums.PixelsTypeint16: np.int16,
    omero_enums.PixelsTypeuint16: np.uint16,
    omero_enums.PixelsTypeint32: np.int32,
    omero_enums.PixelsTypeuint32: np.uint32,
    omero_enums.PixelsTypefloat: np.float32,
    omero_enums.PixelsTypedouble: np.float64,
}


def pad(num, max_len):
  str_num = str(num)
  while len(str_num) < max_len:
    str_num = '0' + str_num
  return str_num


class Omero():
  def __init__(self, host, usr, pwd):
    self.host = host
    self.usr = usr
    self.pwd = pwd
    self.connected = False


  def switch_user_group(self):
    self.conn.SERVICE_OPTS.setOmeroGroup('-1')


  def connect(self):
    print('Connecting to Omero...')
    self.conn = BlitzGateway(self.usr, self.pwd, host=self.host, secure=True)
    if not self.conn.connect():
        self.disconnect()
        print('Connection error')
        raise ConnectionError
    self.conn.c.enableKeepAlive(60)
    self.connected = True
    print(f'Connected as {self.conn.getUser().getName()}')

  def disconnect(self):
      self.conn.close()
      self.connected = False


  def get_slide_names(self, project_id):
    """Return a list of all images from a given project"""
    slides = []
    project = self.conn.getObject('Project', project_id)
    for dataset in project.listChildren():
          for image_object in dataset.listChildren():
              slides.append({"name": image_object.getName(), "id": image_object.getId()})
    return slides

  def get_slides_from_dataset(self, dataset_id):
    """Return a list of all slides in a given dataset"""
    slides = []
    dataset = self.conn.getObject("Dataset", dataset_id)
    for slide in dataset.listChildren():
      slides.append({"name": slide.getName(), "id": slide.getId()})
    return slides
  
  def get_datasets(self, project_id):
    """Return a list of all the datasets in a given project"""
    datasets = []
    project = self.conn.getObject("Project", project_id)
    for dataset in project.listChildren():
      datasets.append({"name": dataset.getName(), "id": dataset.getId()})
    return datasets


  def get_image_object(self, image_id):
    """Return the image object from OMERO given an image ID"""
    return self.conn.getObject("Image", image_id)


  def get_slide_image(self, image_id):
    """Return the image data and name from OMERO given an image ID"""
    image_obj = self.conn.getObject("Image", image_id)
    thumb_x = image_obj.getSizeX() / 20
    thumb_y = image_obj.getSizeY() / 20
    image_bytes = image_obj.getThumbnail((thumb_x, thumb_y))
    data = io.BytesIO(image_bytes)
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data.decode("utf-8"), image_obj.getName()

  def get_image_object(self, image_id):
    image_obj = self.conn.getObject("image", image_id)
    return image_obj


  def get_segment(self, image_id, fx, fy, fw, fh):
    # Obtain segment of a given image given fraction of image x, y, w, h
    image_obj = self.conn.getObject("Image", image_id)
    iw, ih = image_obj.getSizeX(), image_obj.getSizeY()
    sx = int(fx * iw)
    sy = int(fy * ih)
    sw = int(fw * iw)
    sh = int(fh * ih)
    return self.get_tiles(image_obj, (sx, sy, sw, sh))
          

  def get_tiles(self, image_object, xywh):
    # get list of tiles, based on list of tile coordinates
    nchannels = image_object.getSizeC()
    pixels = image_object.getPrimaryPixels()
    dtype = PIXEL_TYPES.get(pixels.getPixelsType().value, None)
    _, _, w, h = xywh
    tile_coords = [(0, c, 0, xywh) for c in range(nchannels)]
    image_gen = pixels.getTiles(tile_coords)
    tile_image = np.zeros((h, w, nchannels), dtype=dtype)
    # merge channels
    for c, image in enumerate(image_gen):
      tile_image[:, :, c] = image
    return tile_image


  def get_ground_truth(self, image_id, annotation_keys):
      image_obj = self.conn.getObject("Image", image_id)
      annotations = {}
      for omero_annotation in image_obj.listAnnotations():
        if omero_annotation.OMERO_TYPE == MapAnnotationI:
          for annotation_key in annotation_keys:
            for annotation in omero_annotation.getMapValue():
              if annotation.name.lower() == annotation_key.lower():
                annotations[annotation_key] = annotation.value
      return annotations


  def get_tile(self, image_id, coords, tile_size):
    image_obj = self.conn.getObject("Image", image_id)
    xywh = (coords[0] * tile_size, coords[1] * tile_size, tile_size, tile_size)
    # get list of tiles, based on list of tile coordinates
    nchannels = image_obj.getSizeC()
    pixels = image_obj.getPrimaryPixels()
    dtype = PIXEL_TYPES.get(pixels.getPixelsType().value, None)
    _, _, w, h = xywh
    tile_coords = [(0, c, 0, xywh) for c in range(nchannels)]
    image_gen = pixels.getTiles(tile_coords)
    tile_image = np.zeros((h, w, nchannels), dtype=dtype)
    
    # merge channels
    for c, image in enumerate(image_gen):
      tile_image[:, :, c] = image
    return tile_image

  def convert_tile_to_tiff(self, image_id, outfilename, coords, tile_size, overwrite=True, compression=None):
        print("getting image object...")
        image_object = self.conn.getObject('Image', image_id)
        print("retrieved image object")
        filetitle=os.path.basename(outfilename)
        print(not os.path.exists(outfilename) or overwrite)
        if not os.path.exists(outfilename) or overwrite:
            print("getting metadata...")
            metadata = self.get_metadata(image_object, filetitle, tile_size)
            print("retrieved metadata")
            xml_metadata = metadata.to_xml()
            print("getting tile...")
            tile_image = self.get_tile(image_id, coords, tile_size)
            print(tile_image.shape)
            print("retrieved tile")
            if tile_image is not None:
                save_tiff(outfilename, tile_image, xml_metadata=xml_metadata)
        print("done")

  def get_metadata(self, image_object, filetitle, tile_size, pyramid_sizes_add=None):
          uuid = f'urn:uuid:{uuid4()}'
          ome = OME(uuid=uuid)

          nchannels = image_object.getSizeC()
          pixels = image_object.getPrimaryPixels()
          channels = []
          channels0 = image_object.getChannels(noRE=True)
          if channels0 is not None and len(channels0) > 0:
              channel = channels0[0]
              channels.append(Channel(
                      id='Channel:0',
                      name=channel.getName(),
                      fluor=channel.getName(),
                      samples_per_pixel=nchannels
                  ))

          tiff_datas = [TiffData(
              uuid=UUID(file_name=filetitle, value=uuid)
          )]

          planes = []
          stage = image_object.getStageLabel()
          if stage is not None:
              for plane in pixels.copyPlaneInfo():
                  planes.append(Plane(
                      the_c=plane.getTheC(),
                      the_t=plane.getTheT(),
                      the_z=plane.getTheZ(),
                      delta_t=plane.getDeltaT(),
                      exposure_time=plane.getExposureTime(),
                      position_x=stage.getPositionX().getValue(),
                      position_x_unit=stage.getPositionX().getSymbol(),
                      position_y=stage.getPositionY().getValue(),
                      position_y_unit=stage.getPositionY().getSymbol(),
                      position_z=stage.getPositionZ().getValue(),
                      position_z_unit=stage.getPositionZ().getSymbol(),
                  ))
              stage_label = StageLabel(
                  name=stage.getName(),
                  x=stage.getPositionX().getValue(),
                  x_unit=stage.getPositionX().getSymbol(),
                  y=stage.getPositionY().getValue(),
                  y_unit=stage.getPositionY().getSymbol(),
                  z=stage.getPositionZ().getValue(),
                  z_unit=stage.getPositionZ().getSymbol()
              )

          image = Image(
              id='Image:0',
              name=image_object.getName(),
              description=image_object.getDescription(),
              acquisition_date=image_object.getAcquisitionDate(),
              pixels=Pixels(
                  size_c=image_object.getSizeC(),
                  size_t=image_object.getSizeT(),
                  # size_x=image_object.getSizeX(),
                  # size_y=image_object.getSizeY(),
                  size_x = tile_size,
                  size_y = tile_size,
                  size_z=image_object.getSizeZ(),
                  physical_size_x=image_object.getPixelSizeX(),
                  physical_size_y=image_object.getPixelSizeY(),
                  physical_size_z=image_object.getPixelSizeZ(),
                  type=image_object.getPixelsType(),
                  dimension_order=pixels.getDimensionOrder().getValue(),
                  channels=channels,
                  tiff_data_blocks=tiff_datas
              ),
          )
          if stage is not None:
              image.stage_label = stage_label
              image.pixels.planes = planes
          ome.images.append(image)

          objective_settings = image_object.getObjectiveSettings()
          if objective_settings is not None:
              objective = objective_settings.getObjective()
              instrument = Instrument(objectives=[
                  Objective(id=objective.getId(),
                            manufacturer=objective.getManufacturer(),
                            model=objective.getModel(),
                            lot_number=objective.getLotNumber(),
                            serial_number=objective.getSerialNumber(),
                            nominal_magnification=objective.getNominalMagnification(),
                            calibrated_magnification=objective.getCalibratedMagnification(),
                            #correction=objective.getCorrection().getValue(),
                            lens_na=objective.getLensNA(),
                            working_distance=objective.getWorkingDistance().getValue(),
                            working_distance_unit=objective.getWorkingDistance().getSymbol(),
                            iris=objective.getIris(),
                            immersion=objective.getImmersion().getValue()
                            )])
              ome.instruments.append(instrument)

              for image in ome.images:
                  image.instrument_ref = InstrumentRef(id=instrument.id)

          if pyramid_sizes_add is not None:
              key_value_map = Map()
              for i, pyramid_size in enumerate(pyramid_sizes_add):
                  key_value_map.m.append(M(k=(i + 1), value=' '.join(map(str, pyramid_size))))
              annotation = MapAnnotation(value=key_value_map,
                                        namespace='openmicroscopy.org/PyramidResolution',
                                        id='Annotation:Resolution:0')
              ome.structured_annotations.append(annotation)

          for omero_annotation in image_object.listAnnotations():
              id = omero_annotation.getId()
              type = omero_annotation.OMERO_TYPE
              annotation = None
              if type == omero.model.MapAnnotationI:
                  key_value_map = Map()
                  for annotation in omero_annotation.getMapValue():
                      key_value_map.m.append(M(k=annotation.name, value=annotation.value))
                  annotation = MapAnnotation(value=key_value_map,
                                            namespace=omero_annotation.getNs(),
                                            id=f'urn:lsid:export.openmicroscopy.org:Annotation:{id}')
              elif type == omero.model.CommentAnnotationI:
                  annotation = CommentAnnotation(value=omero_annotation.getValue(),
                                                namespace=omero_annotation.getNs(),
                                                id=f'urn:lsid:export.openmicroscopy.org:Annotation:{id}')
              if annotation is not None:
                  ome.structured_annotations.append(annotation)
                  for image in ome.images:
                      image.annotation_ref.append(AnnotationRef(id=annotation.id))
          # ome.structured_annotations.append(MapAnnotation(k="confidence", value=))
          return ome


def save_tiff(filename, image, metadata=None, xml_metadata=None, tile_size=None, compression=None,
              pyramid_add=0):
    if xml_metadata is not None:
        xml_metadata_bytes = xml_metadata.encode()
    else:
        xml_metadata_bytes = None

    with TiffWriter(filename, bigtiff=True) as writer:
        
        writer.write(image, photometric='RGB', subifds=pyramid_add,
                     tile=tile_size, compression=compression,
                     metadata=metadata, description=xml_metadata_bytes)
        # writer.write(image, photometric='RGB')

