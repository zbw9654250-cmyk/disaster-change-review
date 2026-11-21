const ROOFS = [
  {
    "id": "b-8d20ecdd66c0",
    "uid": "692353bb-010e-4cfa-a576-d6a45485ba22",
    "tile": "hurricane-harvey_00000304",
    "bbox": [
      -95.58624427559276,
      29.48132106821038,
      -95.58616647784483,
      29.48140749175661
    ],
    "event": "哈维飓风",
    "place": "德克萨斯州",
    "label": "major-damage",
    "grade": "中度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹左下的选区内，灾前画面呈绿色，灾后呈近白色，局部整体变亮。",
    "measure": "建筑足迹左下的选区内，灾前画面呈绿色，灾后呈近白色，局部整体变亮。两个时期的局部都比较均匀，选区内部亮度起伏小。",
    "old": "建筑范围左下区域：图像模糊，无法辨识具体色块、轮廓交界或纹理变化，无法判断灾前灾后差异。",
    "region": "左下",
    "valid": 2116,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-8d20ecdd66c0-pre.png",
        "outline": "b-8d20ecdd66c0-pre-outline.png",
        "detail": "b-8d20ecdd66c0-pre-roi.png",
        "roi": [
          0.3085977777777778,
          0.48544977777777754,
          0.3376984444444444,
          0.5224866666666667
        ],
        "color": "绿色",
        "luma": 138.1,
        "window": [
          139,
          146,
          183,
          202
        ],
        "source": "test/images/hurricane-harvey_00000304_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-harvey_00000304_pre_disaster.json",
        "sceneCrop": [
          0,
          655,
          180,
          835
        ],
        "buildingCrop": [
          39,
          725,
          79,
          765
        ],
        "sourceSha": "8cd61361c0b7541222c50464bb6fa50ddfd341116963d7764a02e4243a1725b8"
      },
      "post": {
        "scene": "b-8d20ecdd66c0-post.png",
        "outline": "b-8d20ecdd66c0-post-outline.png",
        "detail": "b-8d20ecdd66c0-post-roi.png",
        "roi": [
          0.3059524444444444,
          0.48544977777777754,
          0.3350528888888889,
          0.5224866666666667
        ],
        "color": "近白色",
        "luma": 254.7,
        "window": [
          135,
          146,
          179,
          202
        ],
        "source": "test/images/hurricane-harvey_00000304_post_disaster.png",
        "sourceMask": "test/labels/hurricane-harvey_00000304_post_disaster.json",
        "sceneCrop": [
          0,
          655,
          180,
          835
        ],
        "buildingCrop": [
          39,
          725,
          79,
          765
        ],
        "sourceSha": "5e432b8769fc149f0a12d53bd13b455e6fba878c5e2b44750e7a47e1326ada01"
      }
    }
  },
  {
    "id": "b-bbc5120e609a",
    "uid": "3f763c20-2bcb-4bd5-9705-7ea6d6f93519",
    "tile": "hurricane-michael_00000082",
    "bbox": [
      -85.62072252360605,
      30.19705446059857,
      -85.62048317767318,
      30.1971977601368
    ],
    "event": "迈克尔飓风",
    "place": "美国东南部",
    "label": "minor-damage",
    "grade": "轻度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹左下的选区内，灾前画面呈浅灰色，灾后呈青灰色，局部整体变暗。",
    "measure": "建筑足迹左下的选区内，灾前画面呈浅灰色，灾后呈青灰色，局部整体变暗。与灾前相比，选区内不同位置的明暗反差在灾后更加明显。",
    "old": "建筑范围左下区域：灾前浅灰色屋面在灾后变为深色与褐色斑块，上端变化明显，下端未见对应色块，呈现不一致的损伤分布。",
    "region": "左下",
    "valid": 2116,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-bbc5120e609a-pre.png",
        "outline": "b-bbc5120e609a-pre-outline.png",
        "detail": "b-bbc5120e609a-pre-roi.png",
        "roi": [
          0.4195487215189874,
          0.5008382784810127,
          0.44559022151898736,
          0.5261357784810128
        ],
        "color": "浅灰色",
        "luma": 223.8,
        "window": [
          62,
          167,
          97,
          201
        ],
        "source": "test/images/hurricane-michael_00000082_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000082_pre_disaster.json",
        "sceneCrop": [
          642,
          548,
          958,
          864
        ],
        "buildingCrop": [
          760,
          667,
          839,
          746
        ],
        "sourceSha": "14876fa56531f83ba1e295109c360925096edcd9422884854dc51be8b8450311"
      },
      "post": {
        "scene": "b-bbc5120e609a-post.png",
        "outline": "b-bbc5120e609a-post-outline.png",
        "detail": "b-bbc5120e609a-post-roi.png",
        "roi": [
          0.4195487215189874,
          0.4993500284810128,
          0.4530307215189872,
          0.5246477784810125
        ],
        "color": "青灰色",
        "luma": 126.6,
        "window": [
          62,
          165,
          107,
          199
        ],
        "source": "test/images/hurricane-michael_00000082_post_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000082_post_disaster.json",
        "sceneCrop": [
          642,
          548,
          958,
          864
        ],
        "buildingCrop": [
          760,
          667,
          839,
          746
        ],
        "sourceSha": "c7c0e238aa41258cff0070152b14d59f2b9a3e0df2dae441e0198788f57e9815"
      }
    }
  },
  {
    "id": "b-ce3f795ffe12",
    "uid": "fe26adb0-714e-49ee-8c5c-a6c1a97e8d4d",
    "tile": "hurricane-florence_00000396",
    "bbox": [
      -77.8770288519271,
      34.77787241907942,
      -77.87691977830342,
      34.77801173772701
    ],
    "event": "弗洛伦斯飓风",
    "place": "美国东海岸",
    "label": "major-damage",
    "grade": "中度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹右下的选区内，灾前画面呈近白色，灾后呈灰绿色，局部整体变暗。",
    "measure": "建筑足迹右下的选区内，灾前画面呈近白色，灾后呈灰绿色，局部整体变暗。与灾前相比，选区内不同位置的明暗反差在灾后更加明显。",
    "old": "建筑范围右下区域：图像模糊，无法辨识屋面颜色或纹理变化，无法判断灾前灾后差异。",
    "region": "右下",
    "valid": 1978,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-ce3f795ffe12-pre.png",
        "outline": "b-ce3f795ffe12-pre-outline.png",
        "detail": "b-ce3f795ffe12-pre-roi.png",
        "roi": [
          0.5252975000000001,
          0.48139874999999993,
          0.546875,
          0.517113
        ],
        "color": "近白色",
        "luma": 234.1,
        "window": [
          202,
          143,
          231,
          191
        ],
        "source": "test/images/hurricane-florence_00000396_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-florence_00000396_pre_disaster.json",
        "sceneCrop": [
          385,
          724,
          601,
          940
        ],
        "buildingCrop": [
          466,
          805,
          520,
          859
        ],
        "sourceSha": "9c22921160ef3aba2ad9d5f0c0027ffec302ec52d4298214533649d676d81892"
      },
      "post": {
        "scene": "b-ce3f795ffe12-post.png",
        "outline": "b-ce3f795ffe12-post-outline.png",
        "detail": "b-ce3f795ffe12-post-roi.png",
        "roi": [
          0.529762,
          0.48809525000000015,
          0.546875,
          0.5245534999999998
        ],
        "color": "灰绿色",
        "luma": 150.5,
        "window": [
          208,
          152,
          231,
          201
        ],
        "source": "test/images/hurricane-florence_00000396_post_disaster.png",
        "sourceMask": "test/labels/hurricane-florence_00000396_post_disaster.json",
        "sceneCrop": [
          385,
          724,
          601,
          940
        ],
        "buildingCrop": [
          466,
          805,
          520,
          859
        ],
        "sourceSha": "22643f1d1d0c7316622f37359bbadd29c89fb7d7ebd342d9a6adf007013b2019"
      }
    }
  },
  {
    "id": "b-abe0ad891f51",
    "uid": "ca1e284b-91d4-4245-b568-5fd6aee14be7",
    "tile": "socal-fire_00000877",
    "bbox": [
      -118.7556255400668,
      34.05497192811956,
      -118.7553873070423,
      34.05511846177308
    ],
    "event": "南加州山火",
    "place": "加利福尼亚州",
    "label": "no-damage",
    "grade": "无损",
    "mode": "measurement_fallback_no_supported_choice",
    "explain": "建筑足迹右下的选区内，灾前画面呈棕褐色，灾后呈灰褐色。与灾前相比，选区内不同位置的明暗反差在灾后更加明显。",
    "measure": "建筑足迹右下的选区内，灾前画面呈棕褐色，灾后呈灰褐色。与灾前相比，选区内不同位置的明暗反差在灾后更加明显。",
    "old": "建筑范围右下区域：灾前灾后选区图像均极度模糊，无法辨识具体色块或轮廓交界，仅能观察到整体亮度略有变化，但无明确可比特征以判断结构或材料状态。",
    "region": "右下",
    "valid": 2051,
    "state": "changed",
    "facts": [],
    "phase": {
      "pre": {
        "scene": "b-abe0ad891f51-pre.png",
        "outline": "b-abe0ad891f51-pre-outline.png",
        "detail": "b-abe0ad891f51-pre-roi.png",
        "roi": [
          0.5038556266233766,
          0.4968886233766234,
          0.5403138766233766,
          0.5244183733766233
        ],
        "color": "棕褐色",
        "luma": 174.6,
        "window": [
          171,
          166,
          220,
          203
        ],
        "source": "test/images/socal-fire_00000877_pre_disaster.png",
        "sourceMask": "test/labels/socal-fire_00000877_pre_disaster.json",
        "sceneCrop": [
          326,
          104,
          634,
          412
        ],
        "buildingCrop": [
          442,
          219,
          519,
          296
        ],
        "sourceSha": "532c90d3a002601fd7f725906af345ef4f0fc1aff4470484fcaf13ece3c22520"
      },
      "post": {
        "scene": "b-abe0ad891f51-post.png",
        "outline": "b-abe0ad891f51-post-outline.png",
        "detail": "b-abe0ad891f51-post-roi.png",
        "roi": [
          0.5090638766233766,
          0.5020968733766235,
          0.5455221266233765,
          0.5296266233766234
        ],
        "color": "灰褐色",
        "luma": 194.5,
        "window": [
          178,
          173,
          227,
          210
        ],
        "source": "test/images/socal-fire_00000877_post_disaster.png",
        "sourceMask": "test/labels/socal-fire_00000877_post_disaster.json",
        "sceneCrop": [
          326,
          104,
          634,
          412
        ],
        "buildingCrop": [
          442,
          219,
          519,
          296
        ],
        "sourceSha": "0f4a5e8071cd090b2eec5b761592719e886eca866fa979ce54d65d79c90001c4"
      }
    }
  },
  {
    "id": "b-a9482fc5ef0d",
    "uid": "94b7cd10-5850-4d2b-b970-d5fa3342aba8",
    "tile": "hurricane-harvey_00000096",
    "bbox": [
      -95.6405492422034,
      29.8379257310033,
      -95.64034268607182,
      29.83815734784519
    ],
    "event": "哈维飓风",
    "place": "德克萨斯州",
    "label": "destroyed",
    "grade": "重度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹左上的选区内，两期画面的主要色调均为黄灰色。与灾前相比，选区内不同位置的明暗反差在灾后减弱。",
    "measure": "建筑足迹左上的选区内，两期画面的主要色调均为黄灰色。与灾前相比，选区内不同位置的明暗反差在灾后减弱。",
    "old": "建筑范围左上区域：灾前右下缘有亮斑，灾后该亮斑消失，表明局部区域出现明显变化。",
    "region": "左上",
    "valid": 2116,
    "state": "changed",
    "facts": [
      "F2",
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-a9482fc5ef0d-pre.png",
        "outline": "b-a9482fc5ef0d-pre-outline.png",
        "detail": "b-a9482fc5ef0d-pre-roi.png",
        "roi": [
          0.6164965238095238,
          0.4547902619047619,
          0.6461169047619048,
          0.49298461904761903
        ],
        "color": "黄灰色",
        "luma": 112.9,
        "window": [
          138,
          110,
          176,
          159
        ],
        "source": "test/images/hurricane-harvey_00000096_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-harvey_00000096_pre_disaster.json",
        "sceneCrop": [
          688,
          572,
          1024,
          908
        ],
        "buildingCrop": [
          859,
          696,
          947,
          784
        ],
        "sourceSha": "dafb328b4b5ecc0242bf9ee412489d7e4f699b4e29b225bb3e0cf48eea309047"
      },
      "post": {
        "scene": "b-a9482fc5ef0d-post.png",
        "outline": "b-a9482fc5ef0d-post-outline.png",
        "detail": "b-a9482fc5ef0d-post-roi.png",
        "roi": [
          0.6219530476190476,
          0.4625850714285714,
          0.6515731666666666,
          0.5007794285714285
        ],
        "color": "黄灰色",
        "luma": 110.5,
        "window": [
          145,
          120,
          183,
          169
        ],
        "source": "test/images/hurricane-harvey_00000096_post_disaster.png",
        "sourceMask": "test/labels/hurricane-harvey_00000096_post_disaster.json",
        "sceneCrop": [
          688,
          572,
          1024,
          908
        ],
        "buildingCrop": [
          859,
          696,
          947,
          784
        ],
        "sourceSha": "a48ade0333569652708741448ec02883f197a5979abfe0b7e728e80543583eac"
      }
    }
  },
  {
    "id": "b-2862a8406b72",
    "uid": "eb762108-76b3-4cd2-b54c-11d1d02d54c0",
    "tile": "hurricane-michael_00000481",
    "bbox": [
      -85.69653145724949,
      30.19619130765122,
      -85.69640046975756,
      30.19639284262865
    ],
    "event": "迈克尔飓风",
    "place": "美国东南部",
    "label": "minor-damage",
    "grade": "轻度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹右上的选区内，灾前画面呈灰绿色，灾后呈青灰色，局部整体变亮。",
    "measure": "建筑足迹右上的选区内，灾前画面呈灰绿色，灾后呈青灰色，局部整体变亮。与灾前相比，选区内不同位置的明暗反差在灾后更加明显。",
    "old": "建筑范围右上区域：灾前选区可见深色垂直纹理，灾后该纹理消失，但整体色调由灰变蓝，结构轮廓模糊。",
    "region": "右上",
    "valid": 1923,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-2862a8406b72-pre.png",
        "outline": "b-2862a8406b72-pre-outline.png",
        "detail": "b-2862a8406b72-pre-roi.png",
        "roi": [
          0.52678575,
          0.48500451923076926,
          0.54315475,
          0.5207187692307692
        ],
        "color": "灰绿色",
        "luma": 76.1,
        "window": [
          204,
          122,
          226,
          170
        ],
        "source": "test/images/hurricane-michael_00000481_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000481_pre_disaster.json",
        "sceneCrop": [
          52,
          712,
          364,
          1024
        ],
        "buildingCrop": [
          169,
          835,
          247,
          913
        ],
        "sourceSha": "c08f035a2855d9ea6cf8d6b89201e2059b352da8a4d2c9491ee587bd5c85c358"
      },
      "post": {
        "scene": "b-2862a8406b72-post.png",
        "outline": "b-2862a8406b72-post-outline.png",
        "detail": "b-2862a8406b72-post-roi.png",
        "roi": [
          0.52678575,
          0.48277251923076936,
          0.54315475,
          0.5184867692307693
        ],
        "color": "青灰色",
        "luma": 127.3,
        "window": [
          204,
          119,
          226,
          167
        ],
        "source": "test/images/hurricane-michael_00000481_post_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000481_post_disaster.json",
        "sceneCrop": [
          52,
          712,
          364,
          1024
        ],
        "buildingCrop": [
          169,
          835,
          247,
          913
        ],
        "sourceSha": "a1c33ddfe20d2fa759f5e008e17165334a5815dca53382f91489fbb10f5b7e56"
      }
    }
  },
  {
    "id": "b-d64bce19fe1a",
    "uid": "76c97a5c-5848-4a6a-96fa-2dcdd31aca40",
    "tile": "hurricane-florence_00000087",
    "bbox": [
      -77.91419891586384,
      34.54479675435955,
      -77.91402471907648,
      34.54493080408563
    ],
    "event": "弗洛伦斯飓风",
    "place": "美国东海岸",
    "label": "no-damage",
    "grade": "无损",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹右下的选区内，灾前画面呈浅灰色，灾后呈灰绿色，局部整体变暗。",
    "measure": "建筑足迹右下的选区内，灾前画面呈浅灰色，灾后呈灰绿色，局部整体变暗。与灾前相比，选区内不同位置的明暗反差在灾后减弱。",
    "old": "建筑范围右下区域：灾前右下缘有亮斑，灾后该亮斑消失，表明局部区域出现遮挡或屋面变化。",
    "region": "右下",
    "valid": 1368,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-d64bce19fe1a-pre.png",
        "outline": "b-d64bce19fe1a-pre-outline.png",
        "detail": "b-d64bce19fe1a-pre-roi.png",
        "roi": [
          0.5283130175438597,
          0.5253367675438596,
          0.5640272675438596,
          0.5588190175438595
        ],
        "color": "浅灰色",
        "luma": 204.2,
        "window": [
          209,
          205,
          257,
          250
        ],
        "source": "test/images/hurricane-florence_00000087_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-florence_00000087_pre_disaster.json",
        "sceneCrop": [
          734,
          68,
          962,
          296
        ],
        "buildingCrop": [
          819,
          153,
          876,
          210
        ],
        "sourceSha": "c4b199cc08bb344a4feca86da048aff422db17311e603744d668b003da084928"
      },
      "post": {
        "scene": "b-d64bce19fe1a-post.png",
        "outline": "b-d64bce19fe1a-post-outline.png",
        "detail": "b-d64bce19fe1a-post-roi.png",
        "roi": [
          0.5357535175438596,
          0.5186402675438596,
          0.5714677675438599,
          0.5521225175438597
        ],
        "color": "灰绿色",
        "luma": 92.9,
        "window": [
          219,
          196,
          267,
          241
        ],
        "source": "test/images/hurricane-florence_00000087_post_disaster.png",
        "sourceMask": "test/labels/hurricane-florence_00000087_post_disaster.json",
        "sceneCrop": [
          734,
          68,
          962,
          296
        ],
        "buildingCrop": [
          819,
          153,
          876,
          210
        ],
        "sourceSha": "97ed6c0a2857006ea6905880beabaef00bb230c8f936bc09a99a20c4de5bb8d6"
      }
    }
  },
  {
    "id": "b-feb573029a9b",
    "uid": "27da3915-3b4a-4576-8928-e406f4d12283",
    "tile": "hurricane-michael_00000395",
    "bbox": [
      -85.68307223454032,
      30.11848826790315,
      -85.6829767879746,
      30.11856869165485
    ],
    "event": "迈克尔飓风",
    "place": "美国东南部",
    "label": "destroyed",
    "grade": "重度",
    "mode": "visual_fact_selection",
    "explain": "建筑足迹右上的选区内，灾前画面呈棕褐色，灾后呈黄绿色，局部整体变暗。",
    "measure": "建筑足迹右上的选区内，灾前画面呈棕褐色，灾后呈黄绿色，局部整体变暗。灾后选区内可见深浅过渡。",
    "old": "建筑范围右上区域：灾前为浅灰屋面，灾后变为模糊黄绿色，原屋面轮廓与颜色已不可辨，无法确定破坏方式。",
    "region": "右上",
    "valid": 2104,
    "state": "changed",
    "facts": [
      "F1"
    ],
    "phase": {
      "pre": {
        "scene": "b-feb573029a9b-pre.png",
        "outline": "b-feb573029a9b-pre-outline.png",
        "detail": "b-feb573029a9b-pre-roi.png",
        "roi": [
          0.5085977777777777,
          0.47552911111111107,
          0.5343915555555556,
          0.5
        ],
        "color": "棕褐色",
        "luma": 153.6,
        "window": [
          181,
          131,
          220,
          168
        ],
        "source": "test/images/hurricane-michael_00000395_pre_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000395_pre_disaster.json",
        "sceneCrop": [
          74,
          436,
          254,
          616
        ],
        "buildingCrop": [
          144,
          506,
          184,
          546
        ],
        "sourceSha": "019cbaf3bd7c7079bc6004bcf736ebb6b3169f9ea718f06f741065223d81ddff"
      },
      "post": {
        "scene": "b-feb573029a9b-post.png",
        "outline": "b-feb573029a9b-post-outline.png",
        "detail": "b-feb573029a9b-post-roi.png",
        "roi": [
          0.5039682222222223,
          0.4728835555555558,
          0.529762,
          0.4973544444444447
        ],
        "color": "黄绿色",
        "luma": 115.0,
        "window": [
          174,
          127,
          213,
          164
        ],
        "source": "test/images/hurricane-michael_00000395_post_disaster.png",
        "sourceMask": "test/labels/hurricane-michael_00000395_post_disaster.json",
        "sceneCrop": [
          75,
          437,
          255,
          617
        ],
        "buildingCrop": [
          145,
          507,
          185,
          547
        ],
        "sourceSha": "cb8bd80f4f460fcca18731d583ac6b2c039078b3e11c6f91878e4d6f3f69329b"
      }
    }
  }
];
