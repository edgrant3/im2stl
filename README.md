# im2stl

![Best Result](/assets/FinalResult.jpg)

This simple project allows for easy conversion of RGB images into STLs for 3D prints that use backlight (like sunlight streaming in from a window) to display the image. The effect is achieved via slightly translucent filament printed at varying thicknesses (layer heights) across the image plane. Obviously, light-colored PLA is highly reccommended for these prints!

![Subsurface 3D Image Demo](https://github.com/edgrant3/im2stl/blob/main/Demo.gif)

My personal goal with this mini project was to write everything (e.g. the tessellation/triangulation of the mesh) from scratch in Python and get something printed on my new Bambu Labs P1S within a couple evenings. I had a blast putting this together and I'm pleasantly suprised by the final effect!

NOTE: the border in the first image was generated separately in slicing software
