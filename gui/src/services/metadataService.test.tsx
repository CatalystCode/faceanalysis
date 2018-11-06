import { getAll } from './metadataService';

it('get an object back from ALL call', () => {
  const rv = getAll();
  console.log(rv);
  // expect(typeof rv).toBe('object');
});

// it('get single item back', () => {
//   const rv = get('1234');
//   expect(rv).toBeInstanceOf(Object);
//   expect(rv).toMatchObject( { "id": "1234" });
// });
