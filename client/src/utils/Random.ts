export const generateRandomState = () => {
    const randomBytes = new Uint32Array(4); // Generate 4 random 32-bit integers
    window.crypto.getRandomValues(randomBytes); // Use the browser's crypto API for randomness

    // Convert the integers to a hexadecimal string
    return randomBytes.reduce(
        (state, byte) => state + byte.toString(16).padStart(8, '0'),
        ''
    );
};