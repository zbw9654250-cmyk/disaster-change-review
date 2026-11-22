const CHANGE_REGIONS = {
  "oso": {
    "beforeSha256": "c124d94ff6937a0a0893c395efa5950471b7a3c7a1f8062cd8e87a5ef22b0d40",
    "afterSha256": "bcc8d1ecce54f02f558be5931705ba88cd60afed08b59b36a6f5f8922f529bfd",
    "baseline": {
      "method": "single-candidate-v1",
      "rings": [
        [
          28.09,
          28.125,
          51.458,
          39.583
        ]
      ]
    },
    "ours": {
      "method": "multi-candidate-v1",
      "rings": [
        [
          28.09,
          28.125,
          51.458,
          39.583
        ]
      ]
    }
  },
  "mud-creek": {
    "beforeSha256": "4c3db77fc1126fd4b1042f3bfa33f9491ea1c047fc6827efcb0952e28b19658f",
    "afterSha256": "fc6ed9c8cf9b172be830f03d0cfd7ff703c56e139ef772b005fa5324f3fd32d8",
    "baseline": {
      "method": "single-candidate-v1",
      "rings": [
        [
          43.103,
          36.971,
          13.154,
          16.442
        ]
      ]
    },
    "ours": {
      "method": "multi-candidate-v1",
      "rings": [
        [
          43.103,
          36.971,
          13.154,
          16.442
        ]
      ]
    }
  },
  "la-palma": {
    "beforeSha256": "ae79b1e6649c633293f51547b56875628b50aa658aca465f21f60c762f1d8ad4",
    "afterSha256": "88c1e235e35ee9da693bed167240cc8580a16e0fc893cd1bdb4b4d9ea103cd85",
    "baseline": {
      "method": "single-candidate-v1",
      "rings": [
        [
          48.411,
          62.014,
          11.307,
          24.678
        ]
      ]
    },
    "ours": {
      "method": "multi-candidate-v1",
      "rings": [
        [
          48.411,
          62.014,
          11.307,
          24.678
        ],
        [
          43.163,
          38.247,
          12.049,
          9.388
        ]
      ]
    }
  },
  "hurricane-michael": {
    "beforeSha256": "a289a1028dafb1481ce31947c10886733cf0cf8ce2d898d9ee5c6468e7cf6010",
    "afterSha256": "b75e0eab2757f5ace2af3ed860572ba65e39952a4247e8b4e93c00bd29576593",
    "baseline": {
      "method": "single-candidate-v1",
      "rings": [
        [
          77.121,
          43.968,
          17.273,
          31.609
        ]
      ]
    },
    "ours": {
      "method": "reviewed-candidate-subset-v1",
      "rings": [
        [
          48.955,
          52.523,
          12.091,
          18.136
        ]
      ]
    }
  },
  "santa-rosa": {
    "beforeSha256": "2fbbed22bccdad39b62b27918628f22ae179f1bb4627d72aed9c70a0409ea31c",
    "afterSha256": "6a12652c914164b08ed38a008244d275c7d22b9a21ff8af5a428fe8f6adeff83",
    "baseline": {
      "method": "single-candidate-v1",
      "rings": [
        [
          42.23,
          1.875,
          30.735,
          29.338
        ]
      ]
    },
    "ours": {
      "method": "reviewed-candidate-subset-v1",
      "rings": [
        [
          35.314,
          40.625,
          15.647,
          20.956
        ]
      ]
    }
  }
};
