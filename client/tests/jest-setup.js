// include this line for mocking react-native-gesture-handler
import "react-native-gesture-handler/jestSetup";

// Polyfill for setImmediate
if (!global.setImmediate) {
    global.setImmediate = (callback) => setTimeout(callback, 0);
  }
  
  // Polyfill for clearImmediate
  if (!global.clearImmediate) {
    global.clearImmediate = (id) => clearTimeout(id);
  }