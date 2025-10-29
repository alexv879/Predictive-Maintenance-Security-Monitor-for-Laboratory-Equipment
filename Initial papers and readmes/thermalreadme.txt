|-----------------------------------------------------------------------------|
|------------VAP Trimodal People Segmentation Database Info ------------------|
|-----------------------------------------------------------------------------|
|                                                                             |
|   The dataset comprises of 3 scenes, named as follows:                      |
|   1: Meeting room full depth                                                |
|   2: Meeting room constrained depth                                         |
|   3: Canteen                                                                |
|                                                                             |
|   The dataset contains activities of up to three people captured by a       |
|   thermal, depth, and colour sensor. The activity is constrained within the |
|   depth range of the Kinect for Windows V1 sensor in "normal mode".         |
|                                                                             |
|   The cameras used the capturing were                                       |
|   Axis Q1922                                                                |
|   Kinect for Windows V1                                                     |
|                                                                             |
|-----------------------------------------------------------------------------|
|                                                                             |
|   A registration dataset for mapping points between the RGB, depth, and     |
|   thermal modalities are included in the C++ files registrator.h,           |
|   registrator.cpp containing functions for the mapping of points and con-   |
|   tours.                                                                    |
|   Required libraries are OpenCV version 2.4 or higher and the dirent.h      |
|   framework. For compilation on Windows, dirent.h should be downloaded      |
|   separately.                                                               |
|                                                                             |
|   The registration of each scene is dependent on variables stored in        |
|   calibVars.yml which is unique for each scene.                             |
|   The use of the registration algorithm is described in registrator.h       |
|   and demoed in the registrator.cpp main function.                          |
|                                                                             |
|-----------------------------------------------------------------------------|
|                                                                             |
|   The thermal images are stored as a 32bit bitmap of resolution 680x480 px. |
|   The thermal images suffer from radial lens distortion which may be        |
|   rectified by the use of the registrator.h/cpp files in combination with   |
|   the corresponding calibVars.yml file.                                     |
|-----------------------------------------------------------------------------|
|                                                                             |
|   The color images are stored as a 32bit bitmap of resolution 680x480 px.   |
|                                                                             |
|-----------------------------------------------------------------------------|
|                                                                             |
|   The depth images are stored as 16-bit png images where each pixel in      |
|   the image represents the depth of that corresponding pixel in mm.         |
|   Values for the valid depth are in range from 1000 - 3300.                 |
|   Other values are constants specified by the Kinect.                       |
|         -1 - Undefined distance                                             |
|          0 - Too near                                                       |
|       4095 - Too far                                                        |
|                                                                             |
|                                                                             |
|-----------------------------------------------------------------------------|
|-----------------------------------------------------------------------------|