def verify_physical_zero(receipt, thresholds):
    ":"""Verify calibration output receipts against predefined thresholds. returns 'PASS' or 'FAIL'."""
    pass_count = 0
    fail_count = 0

    for key in thresholds:
        if key in receipt:
            if receipt[key] <= thresholds[key]:
                pass_count += 1
            else:
                fail_count += 1

    if fail_count > 0:
        return 'FAIL'
    return 'PASS'

# Example use
if __name__ == '__main__':
    # Example receipt and thresholds
    sample_receipt = {'calibration_value_1': 0.5, 'calibration_value_2': 1.0}
    thresholds = {'calibration_value_1': 0.6, 'calibration_value_2': 1.1}
    result = verify_physical_zero(sample_receipt, thresholds)
    print(f'Calibration result: {result}')