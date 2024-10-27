# coin_grader
predicts the NGC class for a coin based on images



 Here's a breakdown of the key components:

1. Dataset Creation and Web Scraping:
   - `WebScraper` class handles collecting training data
   - Includes methods for downloading images and their corresponding grades
   - You'll need to customize the scraping logic for specific websites

2. Model Implementation:
   - Uses ResNet50 as the base model (pretrained on ImageNet)
   - Modified for coin grading with custom final layers
   - Includes data preprocessing and augmentation
   - Handles 70 possible grades (NGC scale from 1-70)

3. Training Pipeline:
   - Custom `CoinDataset` class for handling coin images
   - Training loop with CrossEntropyLoss and Adam optimizer
   - Includes basic logging of training progress

4. eBay Analysis:
   - `EbayAnalyzer` class for finding potential opportunities
   - Compares predicted grades with listed grades
   - Identifies potentially undervalued coins

To implement this project, you'll need to:

1. Install required packages:
```python
pip install torch torchvision pillow pandas numpy requests beautifulsoup4 selenium
```

2. Customize the `WebScraper` class for your specific data source:
   - Add specific website URLs
   - Implement parsing logic for the structure of your chosen website
   - Handle rate limiting and robots.txt compliance

3. Create a proper training dataset:
   - Collect images of graded coins
   - Ensure proper labeling
   - Consider data augmentation for better results

4. Potential improvements:
   - Add validation split and metrics
   - Implement price prediction
   - Add error handling and logging
   - Add support for different coin types
   - Implement CUDA support for faster training





WebScraper class collects data from Heritage Auctions (ha.com) and PCGS CoinFacts (www.pcgs.com/coinfacts), as they have extensive databases of graded coins with images.

1. Scrapes from two major sources:
   - PCGS CoinFacts: Official grading service with high-quality images and detailed grade information
   - Heritage Auctions: Large auction site with many graded coins

2. Key features:
   - Robust error handling and logging
   - Random delays to avoid rate limiting
   - Image downloading with organized file naming
   - Price extraction and normalization
   - Grade parsing from various formats
   - Data saving in CSV format

3. Additional functionality:
   - Handles multiple image angles per coin
   - Extracts years and denominations
   - Supports multiple coin categories
   - Uses both Selenium (for dynamic content) and requests (for static content)

To use this scraper:

1. Install required packages:
```python
pip install selenium beautifulsoup4 requests pandas
```

2. Install ChromeDriver for Selenium:
   - Download ChromeDriver matching your Chrome version
   - Add it to your system PATH

3. Run the scraper:
```python
scraper = WebScraper()
try:
    # Scrape specific categories
    data = scraper.scrape_pcgs_coinfacts([
        'https://www.pcgs.com/coinfacts/category/morgan-dollars-1878-1921/744'
    ])
    
    # Download images
    scraper.download_images(data, "coin_images")
    
    # Save data
    scraper.save_data(data, 'morgan_dollars.csv')
finally:
    scraper.close()
```

Important notes:
1. This code respects robots.txt and includes reasonable delays
2. You may need to add more error handling for specific edge cases
3. The sites' structures may change, requiring updates to the selectors
4. Consider implementing proxy rotation for larger scraping jobs

