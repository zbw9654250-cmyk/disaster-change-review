"""Synthetic controls for attribution, appearance measurements and missing-data handling."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from PIL import Image, ImageFilter

from evidence import measure, color_name


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.mask=np.zeros((176,176),dtype=np.uint8)
        self.mask[24:144,24:144]=255
        self.base=np.full((176,176,3),[119,104,83],dtype=np.uint8)
        self.case=dict(building_id="roof",image_path="after.png",mask_path="foot.png",
                       pre_image_path="before.png",pre_mask_path="foot.png")
        for name,img in (("before",self.base),("after",self.base),("foot",self.mask)):
            self.save(name,img)

    def save(self,name,img):
        Image.fromarray(img).save(self.root/(name+".png"))

    def test_same_and_exterior(self):
        row=measure(self.case,self.root)
        self.assertEqual(row["change_status"],"stable")
        edited=self.base.copy()
        edited[self.mask==0]=[210,20,10]
        self.save("after",edited)
        out=measure(self.case,self.root)
        self.assertEqual(row["measurement"],out["measurement"])
        self.assertEqual(row["explanation_zh"],out["explanation_zh"])
        self.assertNotEqual(row["image_sha256"],out["image_sha256"])

    def test_positive_and_location(self):
        edited=self.base.copy()
        edited[82:109,53:78]=[22,130,216]
        self.save("after",edited)
        row=measure(self.case,self.root)
        self.assertEqual(row["status"],"ok")
        self.assertEqual(row["change_status"],"changed")
        self.assertEqual(row["evidence_region"]["name"],"bottom_left")
        x,y,X,Y=row["evidence_region"]["post_xyxy"]
        self.assertTrue(x<65/176<X and y<96/176<Y)
        self.assertTrue(all(q["text"]==q["text_zh"] for q in row["measurement"]["facts"]))

    def test_single(self):
        case={k:v for k,v in self.case.items() if not k.startswith("pre_")}
        row=measure(case,self.root)
        self.assertEqual(row["change_status"],"single")
        self.assertIsNone(row["measurement"]["pre"])
        self.assertNotIn("灾前",row["explanation_zh"])

    def test_pure_brightness_change(self):
        self.save("after",self.base+42)
        row=measure(self.case,self.root)
        self.assertEqual(row["change_status"],"changed")
        self.assertIn("变亮",row["explanation_zh"])
        self.assertNotIn("损毁",row["explanation_zh"])

    def test_geometric_perturbation(self):
        before=self.base.copy()
        before[43:110,55:67]=[180,165,135]
        self.save("before",before)
        after=np.asarray(Image.fromarray(np.roll(before,(3,-4),axis=(0,1))).filter(ImageFilter.GaussianBlur(1)))
        self.save("after",after)
        self.save("after_mask",np.roll(self.mask,(3,-4),axis=(0,1)))
        self.case["mask_path"]="after_mask.png"
        row=measure(self.case,self.root)
        self.assertEqual(row["change_status"],"stable")

    def test_black_band_vs_provided_validity(self):
        fixed={"name":"top_left","coords":"normalized_original_image",
               "post_xyxy":[.18,.18,.40,.38],"pre_xyxy":[.18,.18,.40,.38]}
        dark=self.base.copy()
        dark[:85]=0
        self.save("after",dark)
        limited=measure(self.case,self.root,fixed)
        self.assertEqual(limited["status"],"quality_limited")
        self.assertFalse(limited["measurement"]["facts"])
        self.save("valid",np.full_like(self.mask,255))
        self.case["valid_mask_path"]="valid.png"
        good=measure(self.case,self.root,fixed)
        self.assertEqual(good["status"],"ok")
        self.assertEqual(good["measurement"]["post"]["color_zh"],"近黑色")
        self.assertEqual(good["measurement"]["post"]["validity_source"],"provided")

    def test_explicit_missing_data(self):
        self.save("invalid",np.zeros_like(self.mask))
        self.case["pre_valid_mask_path"]="invalid.png"
        self.assertEqual(measure(self.case,self.root)["status"],"quality_limited")

    def test_colors(self):
        self.assertEqual(color_name(np.array([250,250,250])),"近白色")
        self.assertIn("蓝",color_name(np.array([65,85,156])))
        self.assertIn("褐",color_name(np.array([138,97,70])))


if __name__=="__main__":unittest.main()
