export PYTHONPATH=./src:./../../pylibtiff
python ./src/odemis/util/test/img_test.py TestMergeTiles
python ./src/odemis/gui/util/test/img_test.py TestSpatialExport TestSpatialExportAcquisitionData
python ./src/odemis/dataio/test/tiff_test.py TestTiffIO.testExportSmallPyramid TestTiffIO.testExportThinPyramid TestTiffIO.testExportMultiArrayPyramid TestTiffIO.testExportNoWL  TestTiffIO.testAcquisitionDataTIFF TestTiffIO.testExportRead TestTiffIO.testAcquisitionDataTIFFLargerFile
python ./src/odemis/model/test/vattributes_test.py
python ./src/odemis/util/test/conversion_test.py TestConversion.test_get_img_transformation_matrix TestConversion.test_get_tile_md_pos
python ./src/odemis/acq/test/stream_test.py StaticStreamsTestCase StreamTestCase
