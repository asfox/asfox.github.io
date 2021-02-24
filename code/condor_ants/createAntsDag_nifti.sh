#!/bin/bash
# USAGE: createAntsDag_nifti.sh template.nii templateMask.nii subject*.nii > ants_condor.dag

NUM_ITERATIONS=4;
TemplateFile=$1
TemplateImageMask=$2

shift 2
MyImages=`ls $*`

TemplateImage=$TemplateFile
TemplateRoot=${TemplateFile//\.nii/};

iterationCount=1;
while [ $iterationCount -le $NUM_ITERATIONS ]
do
    ouputFileList=""
    
    imageCount=0;
    for Image in $MyImages
    do

        ImageRoot=${Image//\.nii/};
        ImageFile=$ImageRoot.nii
    
        JobName="toTemplate_"$TemplateRoot"_"$iterationCount"Pass_"$ImageRoot

        outputFile=toTemplate_$ImageRoot.nii
        affineFile="toTemplate_"$ImageRoot"Affine.txt"
        warpFile="toTemplate_"$ImageRoot"Warp.nii"
    
        echo "Job $JobName go_ants_nifti.submit"
        echo "VARS $JobName templateFile=\"$TemplateImage\" inputFile=\"$ImageFile\" outputFile=\"$outputFile\" outputAffine=\"$affineFile\" outputWarp=\"$warpFile\" maskFile=\"$TemplateImageMask\" "

        outputFileList[$imageCount]=$outputFile
        outputAffineList[$imageCount]=$affineFile
        outputWarpList[$imageCount]=$warpFile
        JobList[$imageCount]=$JobName
        
        imageCount=$(( $imageCount + 1 ))

    done

    OldTemplateImageMask=""$TemplateImageMask
    TemplateImage=""$TemplateRoot"_"$iterationCount".nii";
    TemplateImageMask=""$TemplateRoot"_"$iterationCount"_mask.nii";

    if [ $iterationCount -ne 1 ]
    then
        parentIteration=$(( $iterationCount - 1 ))
        ParentJobName="createTemplate_"$TemplateRoot"_"$parentIteration
        echo "PARENT $ParentJobName CHILD ${JobList[@]}"
    fi

    JobName="createTemplate_"$TemplateRoot"_"$iterationCount
    echo "Job $JobName go_shapeUpdateTemplate.submit"
    echo "Parent ${JobList[@]} CHILD $JobName"
    outputFileListText=$(printf "%s," "${outputFileList[@]}")
    outputAffineListText=$(printf "%s," "${outputAffineList[@]}")
    outputWarpListText=$(printf "%s," "${outputWarpList[@]}")
    echo "VARS $JobName templateFile=\"$TemplateImage\" RegisteredFiles=\"${outputFileListText%?}\" AffineFiles=\"${outputAffineListText%?}\" WarpFiles=\"${outputWarpListText%?}\" oldMask=\"$OldTemplateImageMask\" newMask=\"$TemplateImageMask\" "

    iterationCount=$(( $iterationCount + 1 ))

done

