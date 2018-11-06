import { ImageProperties, SET_SUBJECT, SET_TARGET, CLEAR_CANDIDATES, ADD_IMAGE } from '../constants';

export const setSubjectImage = (image: ImageProperties) => (
  { type: SET_SUBJECT, payload: image }
);

export const setTargetImage = (image: ImageProperties) => (
  { type: SET_TARGET, payload: image }
);

export const addCandidateImage = (image: ImageProperties) => (
  { type: ADD_IMAGE, payload: image }
);

export const clearCandidates = ( ) => (
  { type: CLEAR_CANDIDATES, payload: null }
);
