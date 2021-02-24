#!/usr/bin/env bash

# Organize my executables.
mkdir ants
mv ./AverageImages ants/
mv ./SetOrigin ants/
mv ./MultiplyImages ants/
mv ./AverageAffineTransform ants/
mv ./WarpImageMultiTransform ants/

# Make sure my executables can be executed.
chmod -R a=wrx ants

# Setup the environment
export HOME=/home/`whoami`
export PATH=$PWD/ants:$PATH

# Rename commandline arguments.
template=$1
outputname=$2
oldMask=$3
newMask=$4
templateRoot=${template//\.nii/}

# set gradient-step constant.
gradientstep=-.15

# move existing transforms into a warps directory.
mkdir warps
mv *Warp.nii warps/
mv *Affine.txt warps/

# Create mean aligned image.
AverageImages 3 ${template} 1 ${outputname}*.nii

# Create mean warp to template space.
AverageImages 3 ${templateRoot}warp.nii 0 warps/${outputname}*Warp.nii

# Multiply warp by gradient-step constant.
MultiplyImages 3 ${templateRoot}warp.nii ${gradientstep} ${templateRoot}warp.nii

# delete template affine.
rm -f ${templateRoot}Affine.txt

# Create mean Affine Transform
AverageAffineTransform 3 ${templateRoot}Affine.txt warps/${outputname}*Affine.txt

# Move template based on the inverse of the mean warp files.
WarpImageMultiTransform 3 ${template} ${template} ${templateRoot}warp.nii ${templateRoot}warp.nii ${templateRoot}warp.nii ${templateRoot}warp.nii -R ${template}

# Move template mask based on the inverse of the mean warp.
SetOrigin 3 ${oldMask} ${oldMask} 0 0 0
WarpImageMultiTransform 3 ${oldMask} ${newMask} ${templateRoot}warp.nii ${templateRoot}warp.nii ${templateRoot}warp.nii ${templateRoot}warp.nii -R ${template}

# Cleanup.
rm -rf ants/ 
rm -rf warps/
rm -rf ${outputname}*.nii


