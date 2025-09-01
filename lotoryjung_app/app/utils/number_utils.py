"""
Number utilities for lottery number processing
"""

import re
from typing import List, Tuple, Optional

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

