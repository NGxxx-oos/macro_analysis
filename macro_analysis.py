import argparse
import csv
import sys
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

# Try to import tabulate, provide helpful error if not installed
try:
    from tabulate import tabulate
except ImportError:
    print("Error: tabulate library is required. Install with: pip install tabulate", file=sys.stderr)
    sys.exit(1)


# ==================== Base Classes ====================

class BaseReporter(ABC):
    """Abstract base class for all reporters."""
    
    @abstractmethod
    def generate(self, data: List[Dict[str, str]]) -> Any:
        """Generate report data from input."""
        pass
    
    @abstractmethod
    def format(self, report_data: Any) -> str:
        """Format report data for display."""
        pass


class ReporterFactory:
    """Factory for creating reporters based on report name."""
    
    _reporters: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a reporter class."""
        def decorator(reporter_class):
            cls._reporters[name] = reporter_class
            return reporter_class
        return decorator
    
    @classmethod
    def create(cls, name: str) -> BaseReporter:
        """Create a reporter instance by name."""
        if name not in cls._reporters:
            available = ", ".join(cls._reporters.keys())
            raise ValueError(f"Unknown report '{name}'. Available reports: {available}")
        return cls._reporters[name]()


# ==================== Reporters ====================

@ReporterFactory.register("average-gdp")
class AverageGDPReporter(BaseReporter):
    
    
    def generate(self, data: List[Dict[str, str]]) -> List[Tuple[str, float]]:
        
        country_gdp = defaultdict(list)
        
        for row in data:
            if 'country' not in row or 'gdp' not in row:
                raise ValueError("CSV must contain 'country' and 'gdp' columns")
            
            try:
                gdp = float(row['gdp'])
                country_gdp[row['country']].append(gdp)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid GDP value: {row.get('gdp')}")
        
        # Calculate averages
        averages = []
        for country, gdps in country_gdp.items():
            avg_gdp = sum(gdps) / len(gdps)
            averages.append((country, avg_gdp))
        
        # Sort by GDP descending
        averages.sort(key=lambda x: x[1], reverse=True)
        
        return averages
    
    def format(self, report_data: List[Tuple[str, float]]) -> str:
        
        headers = ["Country", "Average GDP (billions USD)"]
        table_data = [(country, f"{avg_gdp:.2f}") for country, avg_gdp in report_data]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")


# ==================== File Handling ====================

def read_csv_file(filepath: str) -> List[Dict[str, str]]:

    data = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                raise ValueError(f"CSV file '{filepath}' has no headers")
            
            for row_num, row in enumerate(reader, start=2):
                # Skip completely empty rows
                if all(v == '' for v in row.values()):
                    continue
                data.append(row)
    except csv.Error as e:
        raise ValueError(f"Error parsing CSV file '{filepath}': {e}")
    
    if not data:
        raise ValueError(f"No data found in file '{filepath}'")
    
    return data


def read_csv_files(filepaths: List[str]) -> List[Dict[str, str]]:
    all_data = []
    errors = []
    
    for filepath in filepaths:
        try:
            file_data = read_csv_file(filepath)
            all_data.extend(file_data)
        except FileNotFoundError:
            errors.append(f"File not found: {filepath}")
        except Exception as e:
            errors.append(f"Error reading {filepath}: {e}")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return all_data


# ==================== CLI ====================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze macro-economic data from CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --files data.csv --report average-gdp
  %(prog)s --files file1.csv file2.csv --report average-gdp
        """
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Paths to one or more CSV files with economic data"
    )
    parser.add_argument(
        "--report",
        required=True,
        choices=list(ReporterFactory._reporters.keys()),
        help=f"Type of report to generate. Available: {', '.join(ReporterFactory._reporters.keys())}"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        args = parse_arguments()
        
        # Read data from files
        print(f"Reading {len(args.files)} file(s)...", file=sys.stderr)
        data = read_csv_files(args.files)
        print(f"Loaded {len(data)} records", file=sys.stderr)
        
        if not data:
            print("No data found in the provided files.", file=sys.stderr)
            sys.exit(1)
        
        # Generate report
        reporter = ReporterFactory.create(args.report)
        report_data = reporter.generate(data)
        
        # Display report
        print("\n" + reporter.format(report_data))
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
