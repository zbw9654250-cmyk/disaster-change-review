import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import numpy as np
from PIL import Image
from photometric_context import assess, assess_case

class ContextTests(unittest.TestCase):
    def setUp(self):
        arr=np.random.default_rng(18).integers(30,175,(100,100,3),dtype=np.uint8)
        self.pre=Image.fromarray(arr);self.post=Image.fromarray(arr+24)
        mask=np.zeros((100,100),np.uint8);mask[27:73,28:72]=255
        self.mask=Image.fromarray(mask)
        self.known=dict(same_grid=True,registration_error_px=.2,coverage_fraction=1,pre_coverage_fraction=1)

    def run_case(self,**kw):
        return assess(self.pre,self.post,self.mask,self.mask,**{**self.known,**kw})

    def test_coverage_and_registration(self):
        for inputs in (dict(coverage_fraction=.979),dict(registration_error_px=1.02),
                       dict(same_grid=False),dict(pre_coverage_fraction=None),dict(coverage_fraction=float("nan")),
                       dict(registration_error_px="0"),dict(registration_error_px=float("nan"))):
            self.assertEqual(self.run_case(**inputs)["status"],"reference_insufficient")

    def test_color_compensation(self):
        self.assertEqual(self.run_case()["status"],"consistent_with_surroundings")
        arr=np.array(self.post);arr[42:55,42:55]=20
        self.post=Image.fromarray(arr)
        self.assertEqual(self.run_case()["status"],"local_residual")

    def test_validity_and_texture(self):
        self.assertEqual(self.run_case(post_valid=self.mask)["status"],"reference_insufficient")
        self.pre=Image.new("RGB",(100,100),"black")
        self.assertEqual(self.run_case()["status"],"reference_insufficient")

    def test_file_identity_coords_and_coverage(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            self.pre.save(root/"pre.png");self.post.save(root/"post.png");self.mask.save(root/"mask.png")
            Image.new("L",self.pre.size,255).save(root/"valid.png")
            row=dict(pre_image_path="pre.png",image_path="post.png",mask_path="mask.png",pre_mask_path="mask.png",
                     pre_valid_mask_path="valid.png",valid_mask_path="valid.png",same_pixel_grid=True,
                     registration_error_px=.4,pre_coverage_fraction=1.,coverage_fraction=1.)
            roi=dict(coords="normalized_original_image",pre_xyxy=[.4,.4,.6,.6],post_xyxy=[.4,.4,.6,.6])
            self.assertEqual(assess_case(row,root,roi)["status"],"consistent_with_surroundings")
            self.assertEqual(assess_case(row,root,roi,expected_hashes={"image_sha256":"bad"})["reason"],"source_identity_mismatch")
            self.assertEqual(assess_case(row,root,{**roi,"pre_xyxy":[.1,.1,.3,.3]})["reason"],"evidence_windows_not_colocated")
            self.assertEqual(assess_case({**row,"pre_valid_mask_path":None},root,roi)["reason"],"source_valid_mask_unverified")
            valid=np.ones((100,100),np.uint8)*255
            valid[40:45,40:45]=0
            Image.fromarray(valid).save(root/"valid.png")
            self.assertEqual(assess_case(row,root,roi)["reason"],"valid_window_coverage_below_98pct")
            exif=Image.Exif();exif[274]=6;self.pre.save(root/"pre.png",exif=exif)
            self.assertEqual(assess_case(row,root,roi)["reason"],"unverified_exif_coordinate_system")

if __name__=="__main__":unittest.main()
