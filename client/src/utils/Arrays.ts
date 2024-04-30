export const arraysEqual: (
  a: Record<string, string> | undefined,
  b: Record<string, string> | undefined
) => boolean = (a, b) => {
  // adapted from https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
  if (a === b) return true;
  if (a == undefined || b == undefined) return false;
  if (a.length !== b.length) return false;

  // If you don't care about the order of the elements inside
  // the array, you should sort both arrays here.
  // Please note that calling sort on an array will modify that array.
  // you might want to clone your array first.

  for (var key in b) {
    if (a[key] !== b[key]) {
      return false;
    }
  }
  return true;
};
