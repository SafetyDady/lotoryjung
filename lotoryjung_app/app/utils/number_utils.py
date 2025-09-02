"""
Number utilities for lottery number processing
"""

import re
from typing import List, Tuple, Optional
from itertools import permutations
from datetime import datetime, date, timedelta

def normalize_number(number: str, field: str) -> str:
    """
    Normalize lottery number based on field type
    
    Args:
        number: Input number string
        field: Field type (2_top, 2_bottom, 3_top, tote)
    
    Returns:
        Normalized number string
    """
    # Remove all non-digit characters
    clean_number = re.sub(r'\D', '', str(number))
    
    if field in ['2_top', '2_bottom']:
        # 2-digit numbers: pad with leading zeros
        return clean_number.zfill(2)[-2:]  # Take last 2 digits
    elif field == '3_top':
        # 3-digit numbers: pad with leading zeros
        return clean_number.zfill(3)[-3:]  # Take last 3 digits
    elif field == 'tote':
        # Tote numbers: can be 2 or 3 digits
        if len(clean_number) <= 2:
            return clean_number.zfill(2)
        else:
            return clean_number.zfill(3)[-3:]
    
    return clean_number

def canonicalize_tote(number: str) -> List[str]:
    """
    Canonicalize tote number to all possible permutations
    
    Args:
        number: Input tote number
    
    Returns:
        List of all canonical forms
    """
    normalized = normalize_number(number, 'tote')
    
    if len(normalized) == 2:
        # 2-digit tote: return as is
        return [normalized]
    elif len(normalized) == 3:
        # 3-digit tote: return all unique permutations
        digits = list(normalized)
        permutations = set()
        
        # Generate all permutations
        from itertools import permutations as iter_permutations
        for perm in iter_permutations(digits):
            permutations.add(''.join(perm))
        
        return sorted(list(permutations))
    
    return [normalized]

def validate_number_format(number: str, field: str) -> Tuple[bool, str]:
    """
    Validate number format for specific field
    
    Args:
        number: Input number string
        field: Field type
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    clean_number = re.sub(r'\D', '', str(number))
    
    if not clean_number:
        return False, "กรุณาใส่เลข"
    
    if field in ['2_top', '2_bottom']:
        if len(clean_number) > 2:
            return False, "เลข 2 ตัวต้องไม่เกิน 2 หลัก"
        if int(clean_number) > 99:
            return False, "เลข 2 ตัวต้องอยู่ในช่วง 00-99"
    elif field == '3_top':
        if len(clean_number) > 3:
            return False, "เลข 3 ตัวต้องไม่เกิน 3 หลัก"
        if int(clean_number) > 999:
            return False, "เลข 3 ตัวต้องอยู่ในช่วง 000-999"
    elif field == 'tote':
        if len(clean_number) > 3:
            return False, "เลขโต๊ดต้องไม่เกิน 3 หลัก"
        if len(clean_number) < 2:
            return False, "เลขโต๊ดต้องมีอย่างน้อย 2 หลัก"
    
    return True, ""

def calculate_payout(buy_amount: float, payout_rate: float) -> float:
    """
    Calculate potential payout
    
    Args:
        buy_amount: Amount to buy
        payout_rate: Payout rate multiplier
    
    Returns:
        Potential payout amount
    """
    return buy_amount * payout_rate

def format_currency(amount: float) -> str:
    """
    Format amount as Thai currency
    
    Args:
        amount: Amount to format
    
    Returns:
        Formatted currency string
    """
    return f"{amount:,.2f}"

def parse_amount(amount_str: str) -> Optional[float]:
    """
    Parse amount string to float
    
    Args:
        amount_str: Amount string
    
    Returns:
        Parsed amount or None if invalid
    """
    try:
        # Remove commas and convert to float
        clean_amount = str(amount_str).replace(',', '')
        amount = float(clean_amount)
        
        if amount < 0:
            return None
        
        return amount
    except (ValueError, TypeError):
        return None

def generate_order_number() -> str:
    """
    Generate unique order number
    
    Returns:
        Order number string
    """
    from datetime import datetime
    import random
    
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    random_suffix = f"{random.randint(100, 999)}"
    
    return f"ORD{timestamp}{random_suffix}"

def calculate_lottery_period(order_date: Optional[datetime] = None) -> date:
    """
    Calculate lottery period based on order date
    
    Args:
        order_date: Order date (default: now)
    
    Returns:
        Lottery period date
    """
    from datetime import datetime, date
    import pytz
    
    if order_date is None:
        order_date = datetime.now(pytz.timezone('Asia/Bangkok'))
    
    # Convert to date if datetime
    if isinstance(order_date, datetime):
        order_date = order_date.date()
    
    day = order_date.day
    month = order_date.month
    year = order_date.year
    
    if day <= 16:
        # วันที่ 1-16 → งวดวันที่ 16 ของเดือนเดียวกัน
        return date(year, month, 16)
    else:
        # วันที่ 17-31 → งวดวันที่ 1 ของเดือนถัดไป
        if month == 12:
            return date(year + 1, 1, 1)
        else:
            return date(year, month + 1, 1)

def generate_batch_id(lottery_period: date) -> str:
    """
    Generate batch ID from lottery period
    
    Args:
        lottery_period: Lottery period date
    
    Returns:
        Batch ID string
    """
    return lottery_period.strftime("%Y%m%d")


def generate_2_digit_permutations(number):
    """
    Generate 2 permutations for 2-digit lottery numbers
    
    For 2-digit number like "13", creates:
    [13, 31] - exactly 2 permutations (original and reverse)
    """
    if not number or len(str(number)) != 2:
        return []
    
    num_str = str(number).zfill(2)
    digit1, digit2 = num_str[0], num_str[1]
    
    permutations = []
    
    # Original number
    permutations.append(num_str)
    
    # Reverse  
    reversed_num = digit2 + digit1
    if reversed_num != num_str:  # Only add if different
        permutations.append(reversed_num)
    
    # If digits are the same, we only have 1 permutation
    if digit1 == digit2:
        return [num_str]
    
    return sorted(permutations)  # Return exactly 2 for different digits


def generate_tote_number(number):
    """
    Generate tote number by sorting digits from smallest to largest
    
    Args:
        number: 3-digit number string
    
    Returns:
        Tote number string (digits sorted ascending)
    
    Examples:
        365 → 356 (3 < 5 < 6)
        157 → 157 (1 < 5 < 7) 
        921 → 129 (1 < 2 < 9)
    """
    if not number or len(str(number)) != 3:
        return number
    
    num_str = str(number).zfill(3)
    digits = list(num_str)
    digits.sort()  # Sort from smallest to largest
    
    return ''.join(digits)


def generate_3_digit_permutations(number):
    """
    Generate 6 unique permutations for 3-digit lottery numbers (not including original)
    
    For 3-digit number like "157", creates:
    [157, 175, 517, 571, 715, 751] - exactly 6 permutations
    """
    if not number or len(str(number)) != 3:
        return []
    
    num_str = str(number).zfill(3)
    digits = [num_str[0], num_str[1], num_str[2]]
    
    # Get all unique permutations
    all_perms = set()
    for perm in permutations(digits):
        all_perms.add(''.join(perm))
    
    # Convert to sorted list - should naturally have 6 unique permutations for 3 different digits
    perm_list = sorted(list(all_perms))
    
    # Return exactly 6 permutations
    return perm_list[:6]


def generate_blocked_numbers_for_field(number, field_type):
    """
    Generate all blocked number records for a given number and field type
    
    Args:
        number: The input number (2 or 3 digits)
        field_type: '2_top', '2_bottom', '3_top', 'tote'
    
    Returns:
        List of dictionaries with number permutations
    """
    number_str = str(number).strip()
    
    if not number_str.isdigit():
        return []
    
    records = []
    
    if field_type in ['2_top', '2_bottom'] and len(number_str) == 2:
        # For 2-digit: Generate 2 permutations each for both 2_top and 2_bottom
        permutations_list = generate_2_digit_permutations(number_str)
        
        # Add to 2_top field
        for perm in permutations_list:
            records.append({
                'field': '2_top',
                'number_norm': perm,  # Keep as 2-digit, no padding
                'permutation_type': 'permutation',
                'original_input': number_str
            })
        
        # Add to 2_bottom field  
        for perm in permutations_list:
            records.append({
                'field': '2_bottom',
                'number_norm': perm,  # Keep as 2-digit, no padding
                'permutation_type': 'permutation',
                'original_input': number_str
            })
            
    elif field_type in ['3_top', 'tote'] and len(number_str) == 3:
        # For 3-digit: 6 permutations in 3_top + 1 tote = 7 records total
        permutations_list = generate_3_digit_permutations(number_str)
        
        # First add 6 permutations to 3_top field
        for perm in permutations_list[:6]:  # Take only 6 permutations
            records.append({
                'field': '3_top',
                'number_norm': perm,
                'permutation_type': 'permutation',
                'original_input': number_str
            })
        
        # Then add 1 tote record (sorted digits)
        tote_number = generate_tote_number(number_str)
        records.append({
            'field': 'tote',
            'number_norm': tote_number,
            'permutation_type': 'tote',
            'original_input': number_str
        })
    
    return records


def validate_bulk_numbers(numbers_data):
    """
    Validate bulk numbers input
    
    Args:
        numbers_data: List of dicts with 'number' and 'field' keys
    
    Returns:
        dict with 'valid', 'errors', 'summary' keys
    """
    errors = []
    valid_numbers = []
    stats = {'2_digit': 0, '3_digit': 0, 'total_records': 0}
    
    for i, item in enumerate(numbers_data):
        if not item.get('number') or not item.get('field'):
            continue
            
        number = str(item['number']).strip()
        field = item['field']
        
        # Validate number format
        if not number.isdigit():
            errors.append(f'แถวที่ {i+1}: "{number}" ต้องเป็นตัวเลขเท่านั้น')
            continue
            
        if len(number) < 2 or len(number) > 3:
            errors.append(f'แถวที่ {i+1}: "{number}" ต้องเป็น 2-3 หลัก')
            continue
        
        # Validate field compatibility
        if len(number) == 2 and field not in ['2_top', '2_bottom']:
            errors.append(f'แถวที่ {i+1}: เลข 2 หลัก "{number}" ใช้ได้เฉพาะ 2ตัวบน/2ตัวล่าง')
            continue
            
        if len(number) == 3 and field not in ['3_top', 'tote']:
            errors.append(f'แถวที่ {i+1}: เลข 3 หลัก "{number}" ใช้ได้เฉพาะ 3ตัวบน/โต๊ด')
            continue
        
        # Count expected records
        if len(number) == 2:
            stats['2_digit'] += 1
            stats['total_records'] += 4  # Each 2-digit creates 4 records
        else:
            stats['3_digit'] += 1  
            stats['total_records'] += 7  # Each 3-digit creates 7 records
        
        valid_numbers.append(item)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'valid_numbers': valid_numbers,
        'stats': stats
    }


def preview_bulk_blocked_numbers(numbers_data):
    """
    Generate preview of all numbers that will be created
    
    Returns:
        List of all records that will be inserted into database
    """
    all_records = []
    
    for item in numbers_data:
        records = generate_blocked_numbers_for_field(
            item['number'], 
            item['field']
        )
        
        for record in records:
            record['note'] = item.get('note', '')
            
        all_records.extend(records)
    
    return all_records

