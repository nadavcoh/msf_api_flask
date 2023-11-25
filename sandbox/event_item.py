def find_key_in_data_generator(data, lookup_key):
    if isinstance(data, dict):
        if lookup_key in data:
            yield data[lookup_key]
        
        for _, value in data.items():
            if isinstance(value, (dict, list)):
                yield from find_key_in_data_generator(value, lookup_key)

    elif isinstance(data, list):
        for item in data:
            yield from find_key_in_data_generator(item, lookup_key)

data = {
    "data": {
        "id": "654802508dde86add8789766",
        "startTime": 1699304400,
        "endTime": 1699736400,
        "type": "milestone",
        "name": "Built in the Lab",
        "subName": "Spend Iso-8 Energy and Earn Allied Supply II Orbs",
        "details": "Built in the Lab Milestone\nGain progress in this 5-day event by spending Iso-8 Campaign Energy and earning Allied Supply II Orb fragments from daily Free Claims and the Alliance Donations. Earn incredible rewards including T2 Level 5 Ion Orbs, T2 Level 4 and 5 Ions, and Armory 16, 17, and 18 Orbs. T2 Level 5 Ion Orbs contain up to 5,000,000 T2 Level 5 Ions! You'll also earn points towards the month-long Reverse-Engineer milestone by collecting Vibranium Slabs.",
        "cardArt": "https://assets.marvelstrikeforce.com/key_art/Milestone_BuiltInTheLab_Card_65402e1899c66f8a7723d8ce0a8d7d35a1c6.jpg",
        "popupArt": "https://assets.marvelstrikeforce.com/key_art/Milestone_BuiltInTheLab_Banner_65402e3599c66f8a7723d8cfe6eb430eed46.jpg",
        "milestone": {
            "type": "alliance",
            "typeName": "Alliance",
            "scoring": {
                "description": "Spend Iso-8 Energy and Earn Allied Supply II Orbs",
                "methods": [
                    {
                        "description": "Spend 1 Iso-8 Campaign Energy",
                        "points": 1
                    },
                    {
                        "description": "Earn 1 Allied Supply II Orb Fragment",
                        "points": 1
                    }
                ]
            },
            "brackets": [
                {
                    "id": "default",
                    "objective": {
                        "tiers": {
                            "1": {
                                "goal": 12800,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        }
                                    ]
                                }
                            },
                            "2": {
                                "goal": 25500,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 30000
                                        }
                                    ]
                                }
                            },
                            "3": {
                                "goal": 38300,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        }
                                    ]
                                }
                            },
                            "4": {
                                "goal": 51100,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 40000
                                        }
                                    ]
                                }
                            },
                            "5": {
                                "goal": 63900,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        }
                                    ]
                                }
                            },
                            "6": {
                                "goal": 76700,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 60000
                                        }
                                    ]
                                }
                            },
                            "7": {
                                "goal": 115000,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 60000
                                        }
                                    ]
                                }
                            },
                            "8": {
                                "goal": 127800,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "PROMOTION_CUR",
                                            "quantity": 100
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 10000
                                        }
                                    ]
                                }
                            },
                            "9": {
                                "goal": 153300,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 75000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 10000
                                        }
                                    ]
                                }
                            },
                            "10": {
                                "goal": 178900,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 75000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 15000
                                        }
                                    ]
                                }
                            },
                            "11": {
                                "goal": 204500,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 3000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 80000
                                        },
                                        {
                                            "item": "GACHA_CRATE_GT16_C5_C9_TOKEN_a8d950de",
                                            "quantity": 20000
                                        }
                                    ]
                                }
                            },
                            "12": {
                                "goal": 230100,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 80000
                                        },
                                        {
                                            "item": "GACHA_CRATE_GT17_C1_C8_TOKEN_138df228",
                                            "quantity": 12000
                                        }
                                    ]
                                }
                            },
                            "13": {
                                "goal": 268500,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 4000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 90000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 45000
                                        }
                                    ]
                                }
                            },
                            "14": {
                                "goal": 306900,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 2000
                                        },
                                        {
                                            "item": "ISO8-TIER-0-CURRENCY",
                                            "quantity": 100000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 65000
                                        }
                                    ]
                                }
                            },
                            "15": {
                                "goal": 358100,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 4000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-C-CURRENCY",
                                            "quantity": 100000
                                        }
                                    ]
                                }
                            },
                            "16": {
                                "goal": 409300,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 4000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 65000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-B-CURRENCY",
                                            "quantity": 200000
                                        }
                                    ]
                                }
                            },
                            "17": {
                                "goal": 460500,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "EVTA_META_NOV_A",
                                            "quantity": 4000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-A-CURRENCY",
                                            "quantity": 75000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-C-CURRENCY",
                                            "quantity": 200000
                                        }
                                    ]
                                }
                            },
                            "18": {
                                "goal": 511700,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 10000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-B-CURRENCY",
                                            "quantity": 125000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-C-CURRENCY",
                                            "quantity": 250000
                                        }
                                    ]
                                }
                            },
                            "19": {
                                "goal": 614000,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 12000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-B-CURRENCY",
                                            "quantity": 250000
                                        },
                                        {
                                            "item": "GACHA_CRATE_GT18_C4_C6_TOKEN_e02bf249",
                                            "quantity": 16000
                                        }
                                    ]
                                }
                            },
                            "20": {
                                "goal": 767000,
                                "rewards": {
                                    "allOf": [
                                        {
                                            "item": "GACHA_CRATE_EVENTT2L5_TOKEN_f6ef6b09",
                                            "quantity": 16000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-B-CURRENCY",
                                            "quantity": 500000
                                        },
                                        {
                                            "item": "ISO8-TIER-1-C-CURRENCY",
                                            "quantity": 500000
                                        }
                                    ]
                                }
                            }
                        },
                        "ranges": []
                    }
                }
            ]
        }
    },
    "meta": {
        "version": 1,
        "hashes": {
            "events": "fd46793e86a9957c58e4",
            "drops": "98a3426f6c48aa010e99",
            "locs": "113d79b5852391737883",
            "nodes": "a03184bf8f8a45c569a3",
            "chars": "87be0d5bdb47d646faab",
            "other": "f31a225e4eafd242d0c2",
            "all": "8d36e6d44753988a287d"
        }
    },
    "cache": False
}

result_generator = find_key_in_data_generator(data, "item")
for result in result_generator:
    print(result)