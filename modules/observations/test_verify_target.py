import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from explain_roof import run
from verify_target import save


class TargetVerification(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.case={"building_id":"test-building","uid":"unit","tile":"unit_tile","bbox_lonlat":[1,1,2,2]}
        arr=np.zeros((100,100,3),np.uint8)+130
        m=np.zeros((100,100),np.uint8);m[10:90,10:90]=255
        for ph in ("pre_",""):
            if not ph: arr[30:64,25:70]=225
            for kind,im in (("mask",m),("image",arr)):
                key=ph+kind+"_path";name=ph+kind+".png"
                self.case[key]=name;Image.fromarray(im).save(self.folder/name)

    def test_new_input_and_corrupt_choice(self):
        bank=self.folder/"absent.json"
        with patch("ground_caption.generate",return_value='{"choices":["X"],"reason":"错误"}'):
            row=run(self.case,self.folder,None,None,{},bank)
        self.assertEqual("library_missing",row["retrieval_reason"])
        self.assertEqual("measurement_fallback_verifier_error",row["render_mode"])
        self.assertTrue(row["explanation_zh"])
        self.assertFalse(row["selected_fact_ids"])
        self.assertIsNone(row["reference_case"])

    def test_replay_image_identity(self):
        with self.assertRaisesRegex(ValueError,"input mismatch"):
            run(self.case,self.folder,None,None,{},None,{"building_id":"test-building","image_sha256":"different"})

    def test_output_never_partially_published(self):
        target=self.folder/"out.jsonl"
        def partially_failing():
            yield self.case
            raise RuntimeError("failed")
        with self.assertRaisesRegex(RuntimeError,"failed"):
            save(target,partially_failing())
        self.assertFalse(target.exists())
        save(target,[self.case])
        with self.assertRaises(FileExistsError):
            save(target,[self.case])
        self.assertEqual(json.loads(target.read_bytes()),self.case)


if __name__=="__main__":
    unittest.main()
