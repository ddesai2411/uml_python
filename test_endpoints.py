#!/usr/bin/env python
# coding: utf-8

import uml_lib.ebAPI_lib as eb

print("Testing e-Builder API endpoints...\n")

endpoints = [
    ("Projects", eb.get_project_allData),
    ("Active Projects", eb.get_active_project_all_data),
    ("Budgets", eb.get_budget_all_data),
]

for name, func in endpoints:
    try:
        print(f"Testing {name}...", end=" ")
        func()
        print("✓ SUCCESS")
    except Exception as e:
        print(f"✗ FAILED")
        print(f"  Error: {e}\n")
