display_data.append({
    'Student': parsed.get('student_name', 'Unknown'),
    'Email': email or 'Unknown',
    'Unit': unit,
    'Status': record.get('Status', 'Pending'),
    'Due': due_date.strftime('%Y-%m-%d') if due_date else 'Not set',
    'Past Due': '✅' if is_past_due else '⏰',
    'Submitted': parsed.get('timestamp', record.get('Timestamp', 'Unknown'))
})