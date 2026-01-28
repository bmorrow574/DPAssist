"""
PortfoliOS Setup Validator

This script helps you verify that everything is configured correctly
before running the main system.
"""

import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_check(name, passed, message=""):
    """Print a check result"""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} [{status}] {name}")
    if message:
        print(f"         {message}")


def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    required = (3, 9)
    
    if version >= required:
        print_check(
            "Python Version",
            True,
            f"Python {version.major}.{version.minor}.{version.micro}"
        )
        return True
    else:
        print_check(
            "Python Version",
            False,
            f"Need Python {required[0]}.{required[1]}+, found {version.major}.{version.minor}"
        )
        return False


def check_required_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'utils.py',
        'requirements.txt',
        'config.example.yaml',
    ]
    
    all_exist = True
    for filename in required_files:
        exists = Path(filename).exists()
        print_check(f"Required file: {filename}", exists)
        all_exist = all_exist and exists
    
    return all_exist


def check_config_file():
    """Check if config.yaml exists and is not the example"""
    config_path = Path('config.yaml')
    
    if not config_path.exists():
        print_check(
            "Configuration file (config.yaml)",
            False,
            "File doesn't exist. Copy config.example.yaml to config.yaml"
        )
        return False
    
    # Check if it's just the example file
    with open(config_path, 'r') as f:
        content = f.read()
    
    if 'YOUR_GEMINI_API_KEY_HERE' in content or 'YOUR_GMAIL_APP_PASSWORD' in content:
        print_check(
            "Configuration file (config.yaml)",
            False,
            "File exists but hasn't been configured. Please fill in your details."
        )
        return False
    
    print_check("Configuration file (config.yaml)", True, "File exists and appears configured")
    return True


def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'pandas',
        'yaml',
        'gspread',
        'google.generativeai',
        'selenium',
        'PIL',
        'PyPDF2',
        'docx',
    ]
    
    missing = []
    for package in required_packages:
        # Handle special cases
        if package == 'yaml':
            import_name = 'yaml'
        elif package == 'google.generativeai':
            import_name = 'google.generativeai'
        elif package == 'PIL':
            import_name = 'PIL'
        else:
            import_name = package
        
        try:
            __import__(import_name)
            print_check(f"Package: {package}", True)
        except ImportError:
            print_check(f"Package: {package}", False, "Not installed")
            missing.append(package)
    
    if missing:
        print(f"\n  Missing packages. Install with:")
        print(f"  pip install -r requirements.txt")
        return False
    
    return True


def check_service_account():
    """Check if Google Cloud service account file exists"""
    # First check if config exists
    config_path = Path('config.yaml')
    if not config_path.exists():
        print_check(
            "Google Cloud credentials",
            False,
            "Can't check - config.yaml doesn't exist"
        )
        return False
    
    # Try to load config
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        service_account_file = config.get('google_sheets', {}).get('service_account_file', '')
        
        if not service_account_file:
            print_check(
                "Google Cloud credentials",
                False,
                "No service account file specified in config.yaml"
            )
            return False
        
        if not Path(service_account_file).exists():
            print_check(
                "Google Cloud credentials",
                False,
                f"File not found: {service_account_file}"
            )
            return False
        
        print_check(
            "Google Cloud credentials",
            True,
            f"Found: {service_account_file}"
        )
        return True
        
    except Exception as e:
        print_check(
            "Google Cloud credentials",
            False,
            f"Error checking: {e}"
        )
        return False


def check_google_sheets_connection():
    """Test connection to Google Sheets"""
    try:
        from utils import load_config, connect_to_google_sheets
        
        config = load_config()
        client, worksheet = connect_to_google_sheets(config)
        
        # Try to read the first row
        worksheet.row_values(1)
        
        print_check(
            "Google Sheets connection",
            True,
            f"Connected to: {config['google_sheets']['spreadsheet_name']}"
        )
        return True
        
    except FileNotFoundError as e:
        print_check("Google Sheets connection", False, str(e))
        return False
    except ValueError as e:
        print_check("Google Sheets connection", False, str(e))
        return False
    except Exception as e:
        print_check("Google Sheets connection", False, f"Error: {e}")
        return False


def check_gemini_api():
    """Test Gemini API connection"""
    try:
        from utils import load_config, initialize_gemini, get_gemini_model
        
        config = load_config()
        initialize_gemini(config)
        model = get_gemini_model(config)
        
        # Try a simple test
        response = model.generate_content("Say 'hello' in one word")
        
        print_check(
            "Gemini AI connection",
            True,
            f"API key valid, using model: {config['gemini'].get('model', 'default')}"
        )
        return True
        
    except Exception as e:
        print_check("Gemini AI connection", False, f"Error: {e}")
        return False


def check_email_config():
    """Check email configuration"""
    try:
        from utils import load_config
        
        config = load_config()
        email_config = config.get('email', {})
        
        provider = email_config.get('provider', '')
        teacher_email = email_config.get('teacher_email', '')
        
        if not provider:
            print_check("Email configuration", False, "No provider specified")
            return False
        
        if not teacher_email:
            print_check("Email configuration", False, "No teacher email specified")
            return False
        
        # Check provider-specific settings
        if provider == 'gmail':
            app_password = email_config.get('gmail', {}).get('app_password', '')
            if not app_password or app_password.startswith('YOUR_'):
                print_check("Email configuration", False, "Gmail app password not set")
                return False
        
        elif provider == 'outlook':
            password = email_config.get('outlook', {}).get('password', '')
            if not password or password.startswith('YOUR_'):
                print_check("Email configuration", False, "Outlook password not set")
                return False
        
        elif provider == 'smtp':
            smtp_config = email_config.get('smtp', {})
            if not smtp_config.get('server') or not smtp_config.get('password'):
                print_check("Email configuration", False, "SMTP settings incomplete")
                return False
        
        print_check(
            "Email configuration",
            True,
            f"Provider: {provider}, Email: {teacher_email}"
        )
        return True
        
    except Exception as e:
        print_check("Email configuration", False, f"Error: {e}")
        return False


def main():
    """Run all checks"""
    print_header("PortfoliOS Setup Validator")
    
    print("\nRunning configuration checks...\n")
    
    checks = {
        "Python version": check_python_version(),
        "Required files": check_required_files(),
        "Configuration file": check_config_file(),
        "Dependencies": check_dependencies(),
        "Google Cloud credentials": check_service_account(),
        "Google Sheets connection": check_google_sheets_connection(),
        "Gemini AI connection": check_gemini_api(),
        "Email configuration": check_email_config(),
    }
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! You're ready to run PortfoliOS.")
        print("\nTo start the system, run:")
        print("  python main.py")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nSee SETUP_GUIDE.md for detailed instructions.")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
