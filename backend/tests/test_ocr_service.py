"""
Comprehensive OCR Service Tests
"""

import pytest
import asyncio
import time
import os
from unittest.mock import Mock, patch
import numpy as np
import cv2

from app.services.ocr_service import ocr_service
from app.services.nlp_service import nlp_service
from app.utils.image_processing import image_processor

class TestOCRService:
    
    @pytest.fixture
    def sample_prescription_image(self):
        """Create a sample prescription image for testing"""
        # Create a simple test image with text
        img = np.ones((400, 600, 3), dtype=np.uint8) * 255
        
        # Add some text-like rectangles
        cv2.rectangle(img, (50, 50), (550, 100), (0, 0, 0), -1)
        cv2.rectangle(img, (50, 120), (300, 160), (0, 0, 0), -1)
        cv2.rectangle(img, (50, 180), (400, 220), (0, 0, 0), -1)
        
        # Convert to bytes
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()
    
    @pytest.mark.asyncio
    async def test_text_extraction_basic(self, sample_prescription_image):
        """Test basic OCR text extraction"""
        result = await ocr_service.extract_text(sample_prescription_image)
        
        assert 'text' in result
        assert 'confidence' in result
        assert 'processing_time_ms' in result
        assert isinstance(result['confidence'], float)
        assert 0 <= result['confidence'] <= 1
    
    @pytest.mark.asyncio
    async def test_image_preprocessing(self, sample_prescription_image):
        """Test image preprocessing pipeline"""
        processed_img = image_processor.preprocess_image(sample_prescription_image)
        
        assert processed_img is not None
        assert len(processed_img.shape) == 2  # Should be grayscale
        assert processed_img.dtype == np.uint8
    
    @pytest.mark.asyncio
    async def test_invalid_image_handling(self):
        """Test handling of invalid image data"""
        invalid_data = b"not an image"
        
        result = await ocr_service.extract_text(invalid_data)
        
        assert 'error' in result or result['confidence'] == 0
    
    @pytest.mark.asyncio
    async def test_empty_image_handling(self):
        """Test handling of empty image data"""
        empty_data = b""
        
        result = await ocr_service.extract_text(empty_data)
        
        assert 'error' in result or result['confidence'] == 0
    
    @pytest.mark.asyncio
    async def test_large_image_handling(self, sample_prescription_image):
        """Test handling of large images"""
        # Create a large image
        large_img = np.ones((4000, 6000, 3), dtype=np.uint8) * 255
        _, buffer = cv2.imencode('.jpg', large_img)
        large_image_data = buffer.tobytes()
        
        result = await ocr_service.extract_text(large_image_data)
        
        # Should handle large images gracefully
        assert 'text' in result
    
    @pytest.mark.asyncio
    async def test_processing_time_performance(self, sample_prescription_image):
        """Test OCR processing time meets performance requirements"""
        start_time = time.time()
        
        result = await ocr_service.extract_text(sample_prescription_image)
        
        processing_time = time.time() - start_time
        
        # Should process within 10 seconds for test image
        assert processing_time < 10.0
        assert result.get('processing_time_ms', 0) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, sample_prescription_image):
        """Test concurrent OCR processing"""
        async def process_image():
            return await ocr_service.extract_text(sample_prescription_image)
        
        # Test with 5 concurrent requests
        tasks = [process_image() for _ in range(5)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Should handle concurrent requests efficiently
        assert total_time < 30.0  # 5 images in under 30 seconds
        assert len(results) == 5
        assert all('text' in result for result in results)

class TestNLPService:
    
    @pytest.mark.asyncio
    async def test_prescription_data_parsing(self):
        """Test NLP parsing of prescription text"""
        sample_text = """
        LISINOPRIL 10MG TABLETS
        Rx: 1234567
        Take one tablet daily
        Dr. Smith
        CVS Pharmacy
        NDC: 12345-678-90
        Qty: 30
        """
        
        result = await nlp_service.parse_prescription_data(sample_text)
        
        assert result['medication_name'] is not None
        assert 'lisinopril' in result['medication_name'].lower()
        assert result['dosage'] is not None
        assert '10mg' in result['dosage'].lower()
    
    @pytest.mark.asyncio
    async def test_drug_name_extraction(self):
        """Test drug name extraction from various text formats"""
        test_cases = [
            "METFORMIN 500MG TABLETS",
            "Atorvastatin 20mg",
            "OMEPRAZOLE DR 20 MG",
            "Lisinopril-HCTZ 10-12.5mg"
        ]
        
        for text in test_cases:
            result = await nlp_service.parse_prescription_data(text)
            assert result['medication_name'] is not None
    
    @pytest.mark.asyncio
    async def test_dosage_extraction(self):
        """Test dosage extraction patterns"""
        test_cases = [
            ("Take 10mg daily", "10mg"),
            ("500 mcg twice daily", "500 mcg"),
            ("2.5 mg once daily", "2.5 mg"),
            ("1000 units daily", "1000 units")
        ]
        
        for text, expected_dosage in test_cases:
            result = await nlp_service.parse_prescription_data(text)
            if result['dosage']:
                assert any(char.isdigit() for char in result['dosage'])
    
    def test_text_cleaning(self):
        """Test text cleaning and normalization"""
        dirty_text = "  L1S1N0PR1L   10MG  \n\n  TABLETS  "
        cleaned = nlp_service.clean_text(dirty_text)
        
        assert "LISINOPRIL" in cleaned
        assert "10MG" in cleaned
        assert "TABLETS" in cleaned
        assert cleaned.count(' ') < dirty_text.count(' ')

class TestImageProcessor:
    
    def test_image_validation(self):
        """Test image validation"""
        # Create valid test image
        img = np.ones((200, 300, 3), dtype=np.uint8) * 255
        _, buffer = cv2.imencode('.jpg', img)
        valid_data = buffer.tobytes()
        
        assert image_processor.validate_image(valid_data) == True
        
        # Test invalid data
        invalid_data = b"not an image"
        assert image_processor.validate_image(invalid_data) == False
    
    def test_image_quality_scoring(self):
        """Test image quality assessment"""
        # Create high quality image
        high_quality_img = np.random.randint(0, 255, (400, 600), dtype=np.uint8)
        quality_score = image_processor.get_image_quality_score(high_quality_img)
        
        assert 0 <= quality_score <= 1
        
        # Create low quality (blank) image
        low_quality_img = np.ones((400, 600), dtype=np.uint8) * 128
        low_score = image_processor.get_image_quality_score(low_quality_img)
        
        assert low_score < quality_score
    
    def test_text_region_extraction(self):
        """Test text region detection"""
        # Create image with text-like regions
        img = np.ones((400, 600), dtype=np.uint8) * 255
        
        # Add some black rectangles (simulating text)
        cv2.rectangle(img, (50, 50), (200, 80), 0, -1)
        cv2.rectangle(img, (50, 100), (300, 130), 0, -1)
        
        # Threshold the image
        _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
        
        regions = image_processor.extract_text_regions(thresh)
        
        assert len(regions) >= 2  # Should find at least 2 text regions
        assert all('x' in region for region in regions)
        assert all('y' in region for region in regions)
        assert all('width' in region for region in regions)
        assert all('height' in region for region in regions)

class TestPerformance:
    
    @pytest.mark.asyncio
    async def test_ocr_processing_time(self):
        """Test OCR processing meets performance requirements"""
        # Create standard test image
        img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
        
        # Add some text-like content
        for i in range(10):
            y = 50 + i * 40
            cv2.rectangle(img, (50, y), (400, y + 25), (0, 0, 0), -1)
        
        _, buffer = cv2.imencode('.jpg', img)
        image_data = buffer.tobytes()
        
        start_time = time.time()
        result = await ocr_service.extract_text(image_data)
        processing_time = time.time() - start_time
        
        # Should process within 15 seconds
        assert processing_time < 15.0
        assert result.get('confidence', 0) >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test API performance under concurrent load"""
        async def make_ocr_request():
            img = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', img)
            image_data = buffer.tobytes()
            return await ocr_service.extract_text(image_data)
        
        # Test with 10 concurrent requests
        tasks = [make_ocr_request() for _ in range(10)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Should handle 10 requests within 60 seconds
        assert total_time < 60.0
        
        # Check that most requests succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 8  # At least 80% success rate
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process multiple images
        for _ in range(20):
            img = np.random.randint(0, 255, (800, 1200, 3), dtype=np.uint8)
            processed = image_processor.preprocess_image(cv2.imencode('.jpg', img)[1].tobytes())
            del processed
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_full_prescription_processing_pipeline(self):
        """Test complete prescription processing workflow"""
        # Create realistic prescription image
        img = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Add prescription-like text blocks
        cv2.rectangle(img, (50, 50), (400, 90), (0, 0, 0), -1)  # Drug name
        cv2.rectangle(img, (50, 110), (200, 140), (0, 0, 0), -1)  # Dosage
        cv2.rectangle(img, (50, 160), (300, 190), (0, 0, 0), -1)  # Instructions
        cv2.rectangle(img, (50, 210), (250, 240), (0, 0, 0), -1)  # Doctor
        
        _, buffer = cv2.imencode('.jpg', img)
        image_data = buffer.tobytes()
        
        # Process through full pipeline
        ocr_result = await ocr_service.extract_text(image_data)
        
        if ocr_result.get('text'):
            nlp_result = await nlp_service.parse_prescription_data(ocr_result['text'])
            
            # Verify pipeline completion
            assert 'medication_name' in nlp_result
            assert 'raw_text' in nlp_result
    
    @pytest.mark.asyncio
    async def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline"""
        # Test with corrupted image data
        corrupted_data = b"corrupted image data"
        
        try:
            result = await ocr_service.extract_text(corrupted_data)
            # Should handle gracefully
            assert 'error' in result or result.get('confidence', 0) == 0
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"Unhandled exception: {e}")
    
    @pytest.mark.asyncio
    async def test_quality_feedback_loop(self):
        """Test quality assessment and feedback"""
        # Create high quality image
        high_quality_img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
        
        # Add clear, well-defined text regions
        for i in range(5):
            y = 100 + i * 80
            cv2.rectangle(high_quality_img, (100, y), (600, y + 40), (0, 0, 0), -1)
        
        _, buffer = cv2.imencode('.jpg', high_quality_img)
        high_quality_data = buffer.tobytes()
        
        # Process high quality image
        hq_result = await ocr_service.extract_text(high_quality_data)
        
        # Create low quality image
        low_quality_img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', low_quality_img)
        low_quality_data = buffer.tobytes()
        
        # Process low quality image
        lq_result = await ocr_service.extract_text(low_quality_data)
        
        # High quality should have better confidence
        assert hq_result.get('confidence', 0) >= lq_result.get('confidence', 0)

# Test configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Performance benchmarks
class TestBenchmarks:
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_ocr_throughput_benchmark(self):
        """Benchmark OCR throughput"""
        images = []
        
        # Create 50 test images
        for i in range(50):
            img = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', img)
            images.append(buffer.tobytes())
        
        start_time = time.time()
        
        # Process all images
        tasks = [ocr_service.extract_text(img_data) for img_data in images]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        throughput = len(images) / total_time
        
        print(f"OCR Throughput: {throughput:.2f} images/second")
        
        # Should process at least 1 image per second
        assert throughput >= 1.0
        
        # Check success rate
        successful = sum(1 for r in results if r.get('confidence', 0) > 0)
        success_rate = successful / len(results)
        
        print(f"Success Rate: {success_rate:.2%}")
        assert success_rate >= 0.8  # 80% success rate