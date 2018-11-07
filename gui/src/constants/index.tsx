import { Action } from 'redux';
import { setTargetImage } from 'src/actions';
export const ADD_IMAGE = "ADD_IMAGE";
export const SHOW_IMAGE = "SHOW_IMAGE";
export const SET_SUBJECT = "SET_SUBJECT";
export const SET_TARGET = "SET_TARGET";
export const CLEAR_CANDIDATES = "CLEAR_CANDIDATES";

// export declare interface Actions {
//   type:string;
// }

export interface ImageProperties {
  url: string;
  alt?: string;
  width: number;
  height: number
}

export interface ActionWithPayload<T> extends Action {
  payload: T;
}

export interface ImagePageProps {
  subjectImage: ImageProperties,
  targetImage: ImageProperties,
  candidateImages: ImageProperties[]
}

export interface ImagePageState {
  subjectImage: ImageProperties,
  targetImage: ImageProperties,
  candidateImages: ImageProperties[]
}

export const initialState = {
  subjectImage: {} as ImageProperties,
  targetImage: {} as ImageProperties,
  candidateImages: {} as ImageProperties[]
};

