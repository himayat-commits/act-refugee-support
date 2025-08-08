# Test script for Voiceflow API Integration
# Run this script to test your API endpoints

$baseUrl = "https://act-refugee-support-production.up.railway.app"

Write-Host "Testing ACT Refugee Support API for Voiceflow Integration" -ForegroundColor Green
Write-Host "=" * 60

# Test 1: Health Check
Write-Host "`nTest 1: Health Check" -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "Status: $($health.status)" -ForegroundColor Cyan
Write-Host "Database: $($health.database)" -ForegroundColor Cyan

# Test 2: Main Voiceflow Endpoint - Housing Query
Write-Host "`nTest 2: Voiceflow Endpoint - Housing Query" -ForegroundColor Yellow
$housingBody = @{
    query = "I need help finding accommodation"
    user_id = "test_user_123"
    language = "English"
} | ConvertTo-Json

try {
    $housingResponse = Invoke-RestMethod -Uri "$baseUrl/voiceflow" -Method POST -Body $housingBody -ContentType "application/json"
    Write-Host "Success: $($housingResponse.success)" -ForegroundColor Cyan
    Write-Host "Message: $($housingResponse.message)" -ForegroundColor Cyan
    Write-Host "Resources Found: $($housingResponse.resources.Count)" -ForegroundColor Cyan
    
    if ($housingResponse.resources.Count -gt 0) {
        Write-Host "`nFirst Resource:" -ForegroundColor Magenta
        $firstResource = $housingResponse.resources[0]
        Write-Host "  Name: $($firstResource.name)" -ForegroundColor White
        Write-Host "  Phone: $($firstResource.phone)" -ForegroundColor White
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Test 3: Emergency Services
Write-Host "`nTest 3: Emergency Services Endpoint" -ForegroundColor Yellow
try {
    $emergencyResponse = Invoke-RestMethod -Uri "$baseUrl/search/emergency" -Method POST -ContentType "application/json"
    Write-Host "Success: $($emergencyResponse.success)" -ForegroundColor Cyan
    Write-Host "Message: $($emergencyResponse.message)" -ForegroundColor Cyan
    Write-Host "Emergency Services Found: $($emergencyResponse.resources.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Test 4: Healthcare Query
Write-Host "`nTest 4: Chat Endpoint - Healthcare Query" -ForegroundColor Yellow
$healthcareBody = @{
    query = "I need to see a doctor"
    user_id = "test_user_456"
} | ConvertTo-Json

try {
    $healthcareResponse = Invoke-RestMethod -Uri "$baseUrl/chat" -Method POST -Body $healthcareBody -ContentType "application/json"
    Write-Host "Success: $($healthcareResponse.success)" -ForegroundColor Cyan
    Write-Host "Intent Detected: $($healthcareResponse.metadata.intent)" -ForegroundColor Cyan
    Write-Host "Resources Found: $($healthcareResponse.metadata.results_count)" -ForegroundColor Cyan
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Test 5: Education Query with Language Preference
Write-Host "`nTest 5: Voiceflow Endpoint - Education with Arabic Language" -ForegroundColor Yellow
$educationBody = @{
    query = "Where can I learn English?"
    user_id = "test_user_789"
    language = "Arabic"
    category = "education"
} | ConvertTo-Json

try {
    $educationResponse = Invoke-RestMethod -Uri "$baseUrl/voiceflow" -Method POST -Body $educationBody -ContentType "application/json"
    Write-Host "Success: $($educationResponse.success)" -ForegroundColor Cyan
    Write-Host "Quick Replies Available: $($educationResponse.quick_replies.Count)" -ForegroundColor Cyan
    
    if ($educationResponse.quick_replies.Count -gt 0) {
        Write-Host "Quick Reply Options:" -ForegroundColor Magenta
        foreach ($reply in $educationResponse.quick_replies) {
            Write-Host "  - $reply" -ForegroundColor White
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 60)
Write-Host "All API tests completed!" -ForegroundColor Green
Write-Host "`nYour API is ready for Voiceflow integration at:" -ForegroundColor Yellow
Write-Host $baseUrl -ForegroundColor Cyan
Write-Host "`nMain endpoints for Voiceflow:" -ForegroundColor Yellow
Write-Host "  POST $baseUrl/voiceflow - Main search endpoint" -ForegroundColor White
Write-Host "  POST $baseUrl/chat - Alternative chat endpoint" -ForegroundColor White
Write-Host "  POST $baseUrl/search/emergency - Emergency services" -ForegroundColor White
