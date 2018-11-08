import { getClient } from '../constants';

// Actions
export const ADD_IMAGE = "ADD_IMAGE";
export const SHOW_IMAGE = "SHOW_IMAGE";
export const SET_SUBJECT = "SET_SUBJECT";
export const SET_TARGET = "SET_TARGET";
export const CLEAR_CANDIDATES = "CLEAR_CANDIDATES";


// Service methods
export const getImages = () => {
  const client = getClient();
  //return {
    // type: ADD_IMAGE,
    // payload: { nothing: "nothing"}  };  

  client.get('images')
    .then( (result )=>{
      console.log('got a response');
      return {
        type: ADD_IMAGE,
        
        data: result.data
      };    
    })
    .catch( (reason)=>{
      console.error('died getting /images')
    })
}

export const getImage = (id) => {
  return {
    type: ADD_IMAGE,
    payload: { foo: "bar" }
  };
}





// import { ImageProperties, SET_SUBJECT, SET_TARGET, CLEAR_CANDIDATES, ADD_IMAGE } from '../constants';

// export const setSubjectImage = (image: ImageProperties) => (
//   { type: SET_SUBJECT, payload: image }
// );

// export const setTargetImage = (image: ImageProperties) => (
//   { type: SET_TARGET, payload: image }
// );

// export const addCandidateImage = (image: ImageProperties) => (
//   { type: ADD_IMAGE, payload: image }
// );

// export const clearCandidates = ( ) => (
//   { type: CLEAR_CANDIDATES, payload: null }
// );
