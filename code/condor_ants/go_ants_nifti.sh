#!/usr/bin/env bash

# Organize my executables.
mkdir ants
mv ./ImageMath ants/
mv ./N3BiasFieldCorrection ants/
mv ./SetOrigin ants/
mv ./ANTS ants/
mv ./WarpImageMultiTransform ants/

# Make sure my executables can be executed.
chmod -R a=wrx ants

# Setup the environment
export HOME=/home/`whoami`
export PATH=$PWD/ants:$PATH

# Rename my inputs.
mv $4 templateMask.nii

# Normalize the range of the two nifti files.
ImageMath 3 ./ants/templateImage.nii Normalize $1
ImageMath 3 ./ants/testImage.nii Normalize $2

# Bias correct the images.
N3BiasFieldCorrection  3 ./ants/templateImage.nii ./ants/templateImage_repaired.nii 4
N3BiasFieldCorrection  3 ./ants/testImage.nii ./ants/testImage_repaired.nii 4

# Ensure the origin is zero in all images.
SetOrigin 3 ./ants/templateImage_repaired.nii ./ants/templateImage_repaired.nii 0 0 0
SetOrigin 3 ./ants/testImage_repaired.nii  ./ants/testImage_repaired.nii 0 0 0

# Run ANTS!
ANTS 3 -m CC[./ants/templateImage_repaired.nii,./ants/testImage_repaired.nii, 1,2,-0.95] -t SyN[.10] -r Gauss[2,1] -o $3 -i 100x75x75x50 --use-Histogram-Matching --number-of-affine-iterations 10000x10000x10000x10000x10000 --MI-option 32x16000
# If you want to perform your registration using a weighted mask in tempalte space, you can add '-x templateMask.nii' to the end of the previous line.

# Create testImage in template space.
WarpImageMultiTransform 3 ./ants/testImage_repaired.nii $3 -R $1 ${3/\.nii/}Warp.nii ${3/\.nii/}Affine.txt

