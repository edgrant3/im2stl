# im2stl

This simple project allows for easy conversion of an RGB image to a [lithophane](https://en.wikipedia.org/wiki/Lithophane) in STL or 3MF format. 

Lithophanes use backlight (like sunlight streaming in from a window) to display an image. They take advantage of material thickness to attenuate the backlighting to replicate regions of light and dark in the source image. The effect is achieved via slightly translucent filament printed at varying thicknesses (layer heights) across the image plane. Obviously, light-colored PLA is highly reccommended for these prints!

My personal goal with this mini project was to write everything (e.g. the tessellation/triangulation of the mesh) from scratch (without referencing any other implementation or examples) in Python and get something printed on my new Bambu Labs P1S within a couple evenings. I had a blast putting this together and I'm pleasantly suprised by the final effect! My ongoing effort is to make a simple GUI that allows the users to intuitively select parameters like resulting model dimensions and border settings.

## Final Result - White PLA 3D Print (120mm^2) 
![Best Result](/assets/FinalResult.jpg)

NOTE: the border was generated separately in CAD software

## Source Image
![Source Image](/assets/DSC02666_square.JPG)

## Demo GIF
![Subsurface 3D Image Demo](https://github.com/edgrant3/im2stl/blob/main/Demo.gif)

## Setup Instructions
Jupyter notebook makes for easy prototyping and cell-by-cell execution.

I used Python 3.11 but I don't expect many issues from using another recent Python 3 version.

If on Windows, run setup.bat to create and activate a virtual enviroment into which the dependencies from requirements.txt will be installed.

For Unix/Linux, use setup.sh to achieve the same as above





