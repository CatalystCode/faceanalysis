import { ADD_IMAGE, ImageProperties } from '../constants';

export const addImage = (image: ImageProperties) => (
  { type: ADD_IMAGE, payload: image }
);