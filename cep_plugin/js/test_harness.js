// Test Harness - Test all JSX functions from panel

var TestHarness = (function() {
  var csInterface = new CSInterface();
  var testResults = [];
  
  function runAllTests() {
    testResults = [];
    console.log("[TestHarness] Starting all tests...");
    
    runTest("pingPhotoshop", function(callback) {
      csInterface.evalScript("pingPhotoshop()", callback);
    });
    
    runTest("getPhotoshopInfo", function(callback) {
      csInterface.evalScript("getPhotoshopInfo()", callback);
    });
    
    runTest("createTestDocument", function(callback) {
      csInterface.evalScript("createTestDocument()", callback);
    });
    
    runTest("createDocument", function(callback) {
      csInterface.evalScript("createDocument(10, 10, 300, 'Test Doc', 'RGB')", callback);
    });
    
    runTest("getDocumentInfo", function(callback) {
      csInterface.evalScript("getDocumentInfo()", callback);
    });
    
    runTest("getLayerList", function(callback) {
      csInterface.evalScript("getLayerList()", callback);
    });
    
    runTest("getLayersByPattern", function(callback) {
      csInterface.evalScript("getLayersByPattern('*')", callback);
    });
    
    setTimeout(function() {
      reportResults();
    }, 1000);
  }
  
  function runTest(name, testFn) {
    console.log("[TestHarness] Running:", name);
    
    var startTime = Date.now();
    
    testFn(function(result) {
      var endTime = Date.now();
      var duration = endTime - startTime;
      
      try {
        var data = JSON.parse(result);
        var passed = data.success !== false;
        
        testResults.push({
          name: name,
          passed: passed,
          duration: duration,
          result: data
        });
        
        console.log("[TestHarness]", name, passed ? "✓ PASSED" : "✗ FAILED", "(" + duration + "ms)");
      } catch (e) {
        testResults.push({
          name: name,
          passed: false,
          duration: duration,
          error: e.toString()
        });
        
        console.error("[TestHarness]", name, "✗ FAILED - Parse error:", e);
      }
    });
  }
  
  function reportResults() {
    var passed = testResults.filter(function(r) { return r.passed; }).length;
    var failed = testResults.filter(function(r) { return !r.passed; }).length;
    
    console.log("\n" + "=".repeat(60));
    console.log("TEST RESULTS: " + passed + " passed, " + failed + " failed");
    console.log("=".repeat(60));
    
    testResults.forEach(function(r) {
      var icon = r.passed ? "✓" : "✗";
      console.log(icon + " " + r.name + " (" + r.duration + "ms)");
      if (!r.passed && r.error) {
        console.log("  Error: " + r.error);
      }
    });
    
    updateTestResultsUI(passed, failed);
  }
  
  function updateTestResultsUI(passed, failed) {
    var resultDiv = document.getElementById("test-results");
    if (!resultDiv) return;
    
    resultDiv.innerHTML = '<div class="test-summary"><h3>Test Results: ' + passed + ' passed, ' + failed + ' failed</h3><p class="summary-' + (failed === 0 ? "success" : "error") + '">' + (failed === 0 ? "✓ All tests passed!" : "✗ Some tests failed") + '</p></div><div class="test-details">' + testResults.map(function(r) {
      return '<div class="test-item ' + (r.passed ? "pass" : "fail") + '"><span class="test-icon">' + (r.passed ? "✓" : "✗") + '</span><span class="test-name">' + r.name + '</span><span class="test-duration">' + r.duration + 'ms</span></div>';
    }).join('') + '</div>';
  }
  
  return {
    runAllTests: runAllTests
  };
})();
