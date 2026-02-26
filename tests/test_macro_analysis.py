import pytest
import csv
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.macro_analysis import (
    read_csv_file, read_csv_files, 
    AverageGDPReporter, ReporterFactory,
    main
)


# ==================== File Reader Tests ====================

def test_read_csv_file_valid():
    """Test reading a valid CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("country,year,gdp\n")
        f.write("USA,2023,25462\n")
        f.write("China,2023,17963\n")
        temp_file = f.name
    
    try:
        data = read_csv_file(temp_file)
        assert len(data) == 2
        assert data[0] == {"country": "USA", "year": "2023", "gdp": "25462"}
        assert data[1] == {"country": "China", "year": "2023", "gdp": "17963"}
    finally:
        os.unlink(temp_file)


def test_read_csv_file_empty():
    """Test reading an empty CSV file (headers only)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("country,year,gdp\n")
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError, match="No data found"):
            read_csv_file(temp_file)
    finally:
        os.unlink(temp_file)


def test_read_csv_file_no_headers():
    """Test reading a CSV file without headers."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("USA,2023,25462\n")
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError, match="no headers"):
            read_csv_file(temp_file)
    finally:
        os.unlink(temp_file)


def test_read_csv_file_not_found():
    """Test reading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        read_csv_file("nonexistent.csv")


def test_read_csv_files_multiple():
    """Test reading multiple CSV files."""
    # Create first file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
        f1.write("country,gdp\n")
        f1.write("USA,25462\n")
        file1 = f1.name
    
    # Create second file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
        f2.write("country,gdp\n")
        f2.write("China,17963\n")
        file2 = f2.name
    
    try:
        data = read_csv_files([file1, file2])
        assert len(data) == 2
        assert data[0] == {"country": "USA", "gdp": "25462"}
        assert data[1] == {"country": "China", "gdp": "17963"}
    finally:
        os.unlink(file1)
        os.unlink(file2)


# ==================== Reporter Tests ====================

def test_average_gdp_generate_basic():
    """Test basic average GDP calculation."""
    reporter = AverageGDPReporter()
    
    data = [
        {"country": "USA", "gdp": "25462"},
        {"country": "USA", "gdp": "23315"},
        {"country": "China", "gdp": "17963"},
        {"country": "China", "gdp": "17734"},
    ]
    
    result = reporter.generate(data)
    
    assert len(result) == 2
    assert result[0][0] == "USA"  # Higher average
    assert abs(result[0][1] - 24388.5) < 0.01
    assert result[1][0] == "China"
    assert abs(result[1][1] - 17848.5) < 0.01


def test_average_gdp_generate_with_real_data():
    """Test with actual data from the provided files."""
    reporter = AverageGDPReporter()
    
    # Sample from file1.csv
    data = [
        {"country": "United States", "gdp": "25462"},
        {"country": "United States", "gdp": "23315"},
        {"country": "United States", "gdp": "22994"},
        {"country": "China", "gdp": "17963"},
        {"country": "China", "gdp": "17734"},
        {"country": "China", "gdp": "17734"},
        {"country": "Germany", "gdp": "4086"},
        {"country": "Germany", "gdp": "4072"},
        {"country": "Germany", "gdp": "4257"},
        {"country": "Japan", "gdp": "4230"},
        {"country": "Japan", "gdp": "4235"},
        {"country": "Japan", "gdp": "4936"},
    ]
    
    result = reporter.generate(data)
    
    # Verify order (descending GDP)
    gdps = [gdp for _, gdp in result]
    assert gdps == sorted(gdps, reverse=True)
    
    # Verify calculations
    country_map = {country: avg for country, avg in result}
    assert abs(country_map["United States"] - (25462 + 23315 + 22994) / 3) < 0.01
    assert abs(country_map["China"] - (17963 + 17734 + 17734) / 3) < 0.01


def test_average_gdp_missing_columns():
    """Test error handling when required columns are missing."""
    reporter = AverageGDPReporter()
    
    data = [{"name": "USA", "value": "25462"}]  # Wrong column names
    
    with pytest.raises(ValueError, match="must contain 'country' and 'gdp'"):
        reporter.generate(data)


def test_average_gdp_invalid_gdp():
    """Test error handling with invalid GDP values."""
    reporter = AverageGDPReporter()
    
    data = [{"country": "USA", "gdp": "not_a_number"}]
    
    with pytest.raises(ValueError, match="Invalid GDP value"):
        reporter.generate(data)


def test_average_gdp_format():
    """Test formatting of report."""
    reporter = AverageGDPReporter()
    
    report_data = [
        ("United States", 24388.50),
        ("China", 17848.50),
        ("Germany", 4138.33),
    ]
    
    result = reporter.format(report_data)
    
    assert isinstance(result, str)
    assert "United States" in result
    assert "24388.50" in result
    assert "China" in result
    assert "17848.50" in result
    assert "Germany" in result
    assert "4138.33" in result
    assert "Country" in result
    assert "Average GDP" in result


# ==================== Factory Tests ====================

def test_reporter_factory_valid():
    """Test creating a valid reporter."""
    reporter = ReporterFactory.create("average-gdp")
    assert isinstance(reporter, AverageGDPReporter)


def test_reporter_factory_invalid():
    """Test creating an invalid reporter."""
    with pytest.raises(ValueError, match="Unknown report"):
        ReporterFactory.create("invalid-report")


def test_reporter_factory_registration():
    """Test that reporter is properly registered."""
    assert "average-gdp" in ReporterFactory._reporters
    assert ReporterFactory._reporters["average-gdp"] == AverageGDPReporter


# ==================== CLI Tests ====================

@patch('src.macro_analysis.read_csv_files')
@patch('src.macro_analysis.ReporterFactory.create')
def test_main_success(mock_create, mock_read):
    """Test main function with valid inputs."""
    # Setup mocks
    mock_read.return_value = [{"country": "USA", "gdp": "25462"}]
    
    mock_reporter = MagicMock()
    mock_reporter.generate.return_value = [("USA", 25462.0)]
    mock_reporter.format.return_value = "Formatted table"
    mock_create.return_value = mock_reporter
    
    # Mock command line arguments
    test_args = ["script.py", "--files", "test.csv", "--report", "average-gdp"]
    
    with patch('sys.argv', test_args):
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify calls
            mock_read.assert_called_once_with(["test.csv"])
            mock_create.assert_called_once_with("average-gdp")
            mock_reporter.generate.assert_called_once()
            mock_reporter.format.assert_called_once()
            
            # Should print at least once (the report)
            assert mock_print.call_count >= 1


@patch('src.macro_analysis.read_csv_files')
def test_main_file_not_found(mock_read):
    """Test main with file not found."""
    mock_read.side_effect = FileNotFoundError("File not found: test.csv")
    
    test_args = ["script.py", "--files", "nonexistent.csv", "--report", "average-gdp"]
    
    with patch('sys.argv', test_args):
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                main()
                mock_exit.assert_called_once_with(1)


def test_main_no_files():
    """Test main without required --files argument."""
    test_args = ["script.py", "--report", "average-gdp"]
    
    with patch('sys.argv', test_args):
        with pytest.raises(SystemExit):
            main()


def test_main_invalid_report():
    """Test main with invalid report name."""
    test_args = ["script.py", "--files", "test.csv", "--report", "invalid"]
    
    with patch('sys.argv', test_args):
        with pytest.raises(SystemExit):
            main()


# ==================== Integration Tests ====================

def test_integration_with_sample_files():
    """Integration test using actual sample data."""
    # Create a sample file with data from the example
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("""country,year,gdp,gdp_growth,inflation,unemployment,population,continent
United States,2023,25462,2.1,3.4,3.7,339,North America
United States,2022,23315,2.1,8.0,3.6,338,North America
China,2023,17963,5.2,2.5,5.2,1425,Asia
China,2022,17734,3.0,2.0,5.6,1423,Asia
Germany,2023,4086,-0.3,6.2,3.0,83,Europe
Germany,2022,4072,1.8,8.7,3.1,83,Europe""")
        temp_file = f.name
    
    try:
        # Test the full pipeline
        data = read_csv_file(temp_file)
        reporter = AverageGDPReporter()
        result = reporter.generate(data)
        
        # Verify results
        assert len(result) == 3
        
        country_map = {country: avg for country, avg in result}
        assert abs(country_map["United States"] - (25462 + 23315) / 2) < 0.01
        assert abs(country_map["China"] - (17963 + 17734) / 2) < 0.01
        assert abs(country_map["Germany"] - (4086 + 4072) / 2) < 0.01
        
        # Verify sorting
        assert result[0][0] == "United States"  # Highest GDP
        assert result[1][0] == "China"          # Middle
        assert result[2][0] == "Germany"        # Lowest
        
    finally:
        os.unlink(temp_file)
