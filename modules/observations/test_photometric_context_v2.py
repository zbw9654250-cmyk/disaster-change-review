import unittest
import numpy as np
from PIL import Image

from photometric_context_v2 import assess


class CurveContextTests(unittest.TestCase):
    def setUp(self):
        self.rgb=np.random.default_rng(33).integers(12,239,(140,180,3),dtype=np.uint8)
        self.gamma=255*(self.rgb.astype(float)/255)**1.38
        mask=np.zeros(self.rgb.shape[:2],"uint8");mask[35:105,45:135]=255
        self.mask=Image.fromarray(mask)

    def measure(self,arr,**overrides):
        kw=dict(same_grid=True,registration_error_px=0.,coverage_fraction=1.,pre_coverage_fraction=1.,
                roi=[.30,.30,.45,.45])
        return assess(Image.fromarray(self.rgb),Image.fromarray(np.rint(np.clip(arr,0,255)).astype("uint8")),
                      self.mask,self.mask,**{**kw,**overrides})

    def test_gamma_without_target_edit(self):
        actual=self.measure(self.gamma)
        self.assertEqual(actual["status"],"consistent_with_surroundings")
        self.assertEqual(actual["footprint_followup"]["status"],"no_clear_residual")
        self.assertTrue(all(f["response"]=="power" for f in actual["measurements"]["channel_fits"]))

    def test_localization_outside_original_window(self):
        edited=self.gamma.copy()
        patch=edited[74:90,98:117];patch[:]=np.where(patch<128,patch+60,patch-60)
        actual=self.measure(edited)
        self.assertEqual(actual["status"],"consistent_with_surroundings")
        self.assertEqual(actual["footprint_followup"]["status"],"local_residual")
        box=actual["footprint_followup"]["residual_xyxy"]
        self.assertTrue(box[0]<107/180<box[2] and box[1]<82/140<box[3])

    def test_reject_spatially_incompatible_reference_and_missing_registration(self):
        arr=self.gamma.copy();arr[:,:90]+=30;arr[:,90:]-=30
        self.assertEqual(self.measure(arr)["status"],"reference_insufficient")
        self.assertEqual(self.measure(self.gamma,registration_error_px=None)["status"],"reference_insufficient")


if __name__=="__main__":unittest.main()
