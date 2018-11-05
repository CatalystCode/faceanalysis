import * as React from 'react';
// import { Image } from 'reactstrap';
// import { Image } from 'react-dom'
import './ImageViewer.css';

export interface Props {
  url: string;
  alt?: string;
  width: number;
  height: number
}

export const ImageViewer = (props: Props) => {
  const img = new Image(props.height, props.width);
  img.src = props.url;
  

  return (
    <div className="img-right">
      <img src={img.src} height={img.height} width={img.width} />
    </div>
  )
}


