function [d]=fmris_write_image(d,Z,T)

% (c) John Aston & Roger Gunn

file = deblank(d.file_name);
if ~(file(1)=='/' | file(2)==':')
   if file(1:2)=='./'
      file=[pwd file(3:length(file))];
   else
      file=[pwd '/' file];
   end
end

[base,ext]=fileparts2(file);
d.file_name=[base ext];
   
switch lower(ext)
case '.mnc'
   if nargin == 3
      fmris_write_minc(d,Z,T);
   else
      fmris_write_minc(d);
   end
case '.img'
   if nargin == 3
      fmris_write_analyze(d,Z,T);
   else
      fmris_write_analyze(d);
   end
case '.brik'
   if nargin == 3
      fmris_write_afni(d,Z,T);
   else
      fmris_write_afni(d);
   end
case '.nii'
   if nargin == 3
      SurfStatWriteVol1(d,Z,T);
   else
      SurfStatWriteVol1(d);
   end
otherwise
   ['Unknown file extension']
end

return


