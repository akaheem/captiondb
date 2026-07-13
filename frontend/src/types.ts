export interface Scene {
  id: string;
  timeStart: string; // e.g. "00:00"
  timeEnd: string; // e.g. "00:10"
  secondsStart: number;
  secondsEnd: number;
  title: string;
  thumbnail: string;
  transcript: string;
  tags: string[];
  status: 'Synced' | 'Playing' | 'Processing';
  captions: {
    formal: string;
    sarcastic: string;
    humorousTech: string;
    humorousNonTech: string;
    audio: string;
    none: string;
    selectedTone: 'formal' | 'sarcastic' | 'humorousTech' | 'humorousNonTech' | 'audio' | 'none';
  };
}

export interface VideoProject {
  id: string;
  name: string;
  size: string;
  duration: string;
  durationSeconds: number;
  status: 'Processing' | 'Queued' | 'Completed' | 'Idle';
  progress: number;
  fps: string;
  codec: string;
  resolution: string;
  thumbnail: string;
  scenes: Scene[];
}

export interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  sourceLink?: {
    sceneId: string;
    timestampLabel: string;
    seconds: number;
  };
}
