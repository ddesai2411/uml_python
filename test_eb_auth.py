import traceback
from urllib.parse import quote
import uml_lib.ebAPI_lib as eb


def test_endpoint(cfg, endpoint_name, endpoint_path):
    url = cfg.hostname + endpoint_path
    try:
        data = eb.get_request(url)
        print(f"✓ {endpoint_name} ok")
        return True
    except Exception as e:
        print(f"✗ {endpoint_name} failed: {type(e).__name__}: {e}")
        return False


def main():
    cfg = eb.get_config()
    print("auth ok", eb.get_ebToken())
    print()

    endpoints = [
        ("Projects", "/api/v2/Projects?$format=json"),
        (
            "ActiveProjects",
            "/api/v2/Projects?$format=json&$filter="
            + quote("status eq 'Active'", safe="'"),
        ),
        ("Budgets", "/api/v2/Budgets?$format=json"),
        ("Commitments", "/api/v2/Commitments?$format=json"),
        ("Invoices", "/api/v2/CommitmentInvoices?$format=json"),
        ("FundingRules", "/api/v2/FundingRules?$format=json"),
        ("Companies", "/api/v2/Companies?$format=json"),
        ("CommitmentItems", "/api/v2/CommitmentItems?$format=json"),
        ("FundingSources", "/api/v2/FundingSources?$format=json"),
    ]

    results = []
    for endpoint_name, endpoint_path in endpoints:
        result = test_endpoint(cfg, endpoint_name, endpoint_path)
        results.append((endpoint_name, result))

    print()
    print("Summary:")
    for endpoint_name, result in results:
        status = "✓ OK" if result else "✗ BLOCKED"
        print(f"  {status}: {endpoint_name}")


if __name__ == "__main__":
    main()
