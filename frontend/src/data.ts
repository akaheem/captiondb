import { VideoProject, Scene } from './types';

export const SAMPLE_PROJECTS: VideoProject[] = [
  {
    id: 'surveillance-cam',
    name: 'surveillance_cam_04.mp4',
    size: '1.8 GB',
    duration: '00:45:00',
    durationSeconds: 2700,
    status: 'Completed',
    progress: 100,
    fps: '30fps',
    codec: 'H.264',
    resolution: '1080p',
    thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCWJj-pn7QUMuCngvas3WnWqAQv6LnzCBXK5rLWyWQgLkKxZWzpBIX15uOlVsGP4GwXpz4c-WTRgnp3CtRcXGVl_PVLI5uXRVfCQYp5pnylc8ZKirYp-MGRnrpLchrDa-93HxYRc1DPpc1iQg-hWubxGE--Mv_W7QCXEmncf9B_tQfzrgCpMovg_ae2Wy42t1lX1zctTIFG06PJp5LrPQjabmNb4ZEr268JGeQ3p7t7spk0G7qN_e8ASqMEefcOX8eYyuovZ8DeqH3I',
    scenes: [
      {
        id: 'scene-1',
        timeStart: '00:00',
        timeEnd: '00:10',
        secondsStart: 0,
        secondsEnd: 10,
        title: 'Empty Alleyway',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuABwepv0tIXuvpw9Q0bmd95hIlnrsze5aqhZwmdtnOXgKfEUE2weJJFPu-Efw40ctorM6SHADYuGxslrrsPO3PH-aUeD7S880BOJshE28GHLCrkH_KFE_mw_SdN6Kv6KWGsYLGRVobuXWuHsfoVnVNUWH_tbzRQMxQf8oC0CLatsa3rtGWyXsfTw1ih2BP-He5wC8M9AJ4NNHKNTWk7AoxkNvql5K5hXEUkr3Ynu-7s3mL8JgmHtjNFy3oxXagPtdse77iC-XiVgKdj',
        transcript: 'Static environment. No significant movement detected in frame. Ambient noise only. Lighting conditions stable.',
        tags: ['#static', '#empty', '#night'],
        status: 'Synced',
        captions: {
          formal: 'The camera captures a static view of an empty urban alleyway at night.',
          sarcastic: 'Absolutely thrilling footage of static night air and a completely empty road.',
          humorousTech: 'Zero organic velocity vectors detected in the localized spatial grid.',
          humorousNonTech: 'Quiet night where even the wind seems to have taken the day off.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      },
      {
        id: 'scene-2',
        timeStart: '00:12',
        timeEnd: '00:45',
        secondsStart: 12,
        secondsEnd: 45,
        title: 'Subject Entry',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAR-1DeOWgTMzWAGyn1Buam5mOGSnJ5qDE3fDolO7hmklTqf9GBG2TOfug3B5raAccTPbA0nhwq8NZ3Fn9BX8AYRS-7fvrDDxELVPI5FZwGU-glObU_tcNKFyHJInB2bTEjpyhxIiRNfyyfM9tPN-iRgKbsrRUEPBmxEh3BCh10VLTxHOKJ87LvsrBHG-cPzjBax9QuxKuSrxg6lr-m-I4rOqEp6ODc0v7lPhTNL1xmKdJzN1RiSqgAj9qyUkr4USYO_BJcvm10Jnak',
        transcript: 'Subject 1 (Vehicle) enters frame from North. Bounding box confidence 98.4%. License plate scan initiated. Mild audio spike detected at 00:14.',
        tags: ['#vehicle', '#entry', '#scan'],
        status: 'Playing',
        captions: {
          formal: 'The subject is walking through a dense forest during sunset.',
          sarcastic: 'Local human discovers trees. Groundbreaking.',
          humorousTech: 'Biological entity traversing a high-density vertical chlorophyll array.',
          humorousNonTech: 'A guy getting his steps in while the sun clocks out.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      },
      {
        id: 'scene-3',
        timeStart: '00:46',
        timeEnd: '01:20',
        secondsStart: 46,
        secondsEnd: 80,
        title: 'Pedestrian Motion',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD9LopW6w6zVaRlZ8pilGySt2s--Jkn8rvIrIfi2XW7YPbSro8Cw92TFTcm4bkmJgrvxBlp8RnA8anm047yMhDdhQsdwVOm4FQvXZz19TDxAmv4-miWEXclUm-qghGqVLnpmN8Abu4EUBQnjHrMWEcvv-8pI02Cuwb2UrSv-HFwd-D0MQYYpyuHsGWIySLFADQHNO6YrBpNBC4RnPbbbvsXuJJH821YQyPrmFV1HsMcsBPwCJM-GQBt7-FG0AGf5dpzGOaUmQ_jYvP9',
        transcript: 'Secondary motion detected in background. Pedestrian suspected. Analyzing trajectory data and resolving low-light noise artifacts.',
        tags: ['#pedestrian', '#motion', '#low-light'],
        status: 'Processing',
        captions: {
          formal: 'A distant figure is observed moving across the background of the industrial dock.',
          sarcastic: 'A blurry blob wanders in the shadows. Suspense levels remain at absolutely zero.',
          humorousTech: 'Secondary organic matter executing low-velocity transit through shadows.',
          humorousNonTech: 'Just someone taking an extremely mysterious stroll in a dark, creepy dock.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      },
      {
        id: 'scene-4',
        timeStart: '01:22',
        timeEnd: '02:05',
        secondsStart: 82,
        secondsEnd: 125,
        title: 'Loading Dock Detail',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAjqy3bWKRXi6Zm5FOzFAlUxDls9HNlKtemfrVexESslKjcnihYDtkok4BmRdtVi6-G992RroF0aeiZ4F_jUtkuzTrlOWaVK57-Q0k0GQVPLAF636H21wTWETD5UPIhvmTqI9SU01496CBlupYahTXpO_as7PGTkYrMQpsMdM5rWs_8XlcGMSKEd731LtChORQTIV1k-kgwL1_dELBbNL6xAX7nmDOyuM1bq_FQsREg5n0EeHyMGPQxDtOmG32jhWLT8PN3JgwlrDzd',
        transcript: 'High contrast security still of loading dock area. Geometric tracking confirms cargo gate remains locked.',
        tags: ['#loading-dock', '#lock-check', '#gate'],
        status: 'Synced',
        captions: {
          formal: 'The camera feed monitors the locked loading gate, ensuring compound security.',
          sarcastic: 'Still locked. Yes, the gate is still exactly where we left it.',
          humorousTech: 'Verification protocols confirm continuous status barrier lock state.',
          humorousNonTech: 'Checking on a gate. Excitement level: watching paint dry.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      },
      {
        id: 'scene-5',
        timeStart: '02:10',
        timeEnd: '02:40',
        secondsStart: 130,
        secondsEnd: 160,
        title: 'License Plate Scan',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCyb_ttrmgYyc2OU3dA5xEDsxXb6CBdsm1C9reQ-atL9BLnN1A7Cczl1aj1iE18wgs3IRjPz25aKYUiwX1nWbGbrBxhU9PLc7fRsgXbuFupTKWRlh9eKBp601Wdj90w7kC7ZuudCDJegvHIceMn3VgKvZzt8ylTrOJTFmWhoxIsjd0h7VW6lUmEYhYsHLgVqkhMqzWt180QsbIbQo6J0_kWAhdvPU1S_W9YuiMlp1oQONbotPMNjTnU-WaA_BHP1MnFC3sl1n7gEszT',
        transcript: 'AI Optical Character Recognition scanning license plate: California 7RJK429. Verification matches database entry.',
        tags: ['#ocr', '#plate-scan', '#verified'],
        status: 'Synced',
        captions: {
          formal: 'System initiates high-resolution scan of license plate number 7RJK429.',
          sarcastic: 'Zooming in on a license plate because cyber-spying is the new neighborhood watch.',
          humorousTech: 'OCR algorithm translating retroreflective alphanumeric characters to ASCII string.',
          humorousNonTech: 'Reading a license plate: 7RJK429. Turns out it is indeed a car.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      }
    ]
  },
  {
    id: 'nature-doc',
    name: 'nature_doc.mp4',
    size: '1.2 GB',
    duration: '00:12:45',
    durationSeconds: 765,
    status: 'Processing',
    progress: 85,
    fps: '24fps',
    codec: 'H.265',
    resolution: '4K',
    thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDi-NuXcTV5R4Zj_oErfmSDncrDfgZHnwsc2v4rWFgK3s38f_PD2vdpb3C_9GR5H5GAHOvaIg6J4NCXCLbo_R6eSWDP-lXesFZsgLIciBiEalKP1axDi8gGAE7XxefH-fE6hD8n6EJMaqamZBagCHGxPwbkylF4tsxxqrVTfv6VtB74bOWWNoCTO60tWRpeIus8x7Z21Q-sqXCrHmOOzKOYdx6iMRfyxJePXwzeWuMwru4qBZjxIF2MaV5SK-bk1StEebJEmdJ3zM6N',
    scenes: [
      {
        id: 'nature-1',
        timeStart: '00:00',
        timeEnd: '04:15',
        secondsStart: 0,
        secondsEnd: 255,
        title: 'Misty Forest Morning',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDi-NuXcTV5R4Zj_oErfmSDncrDfgZHnwsc2v4rWFgK3s38f_PD2vdpb3C_9GR5H5GAHOvaIg6J4NCXCLbo_R6eSWDP-lXesFZsgLIciBiEalKP1axDi8gGAE7XxefH-fE6hD8n6EJMaqamZBagCHGxPwbkylF4tsxxqrVTfv6VtB74bOWWNoCTO60tWRpeIus8x7Z21Q-sqXCrHmOOzKOYdx6iMRfyxJePXwzeWuMwru4qBZjxIF2MaV5SK-bk1StEebJEmdJ3zM6N',
        transcript: 'Dense morning fog rolls across a forest valley. Highly diffused morning sunlight casts a soft blue-green tone across the ancient redwood branches.',
        tags: ['#nature', '#fog', '#dawn', '#redwoods'],
        status: 'Synced',
        captions: {
          formal: 'Morning mist settling over a thick redwood forest at dawn.',
          sarcastic: 'Vague green shapes covered in clouds. Truly groundbreaking foliage action.',
          humorousTech: 'High density aerosolized H2O droplets intersecting botanical columns.',
          humorousNonTech: 'Trees getting a misty bath while the sun attempts to wake up.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      }
    ]
  },
  {
    id: 'city-vlog',
    name: 'city_vlog.mp4',
    size: '450 MB',
    duration: '00:08:30',
    durationSeconds: 510,
    status: 'Queued',
    progress: 0,
    fps: '60fps',
    codec: 'ProRes',
    resolution: '1080p',
    thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAhs9y4osdeP-4Zn6mBjxpbcj6HYoOQ5dM8LYfRUYT78tWbq3iuhcwUb-1n_xDmmINGd8Xkr2Ye7ymIatilQWjIKLTBkrBbegI_NYb1w7MqgsXMVk4oKKHw5dZseO3jSKoGcar867LfFFUFVPQU49wwilKnyU3ZMXhOPuAHQ1GV6gKh-0vHS31uiOilGxx6tOyUCc3GQ28usOTM5s0sa8N-GkxD4y7gbXwUdytX5UW70f2mC9Ax6QgaNI1_oeNFqem1w7TwEKz9bAHx',
    scenes: [
      {
        id: 'vlog-1',
        timeStart: '00:00',
        timeEnd: '02:00',
        secondsStart: 0,
        secondsEnd: 120,
        title: 'Neon Streets Transit',
        thumbnail: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAhs9y4osdeP-4Zn6mBjxpbcj6HYoOQ5dM8LYfRUYT78tWbq3iuhcwUb-1n_xDmmINGd8Xkr2Ye7ymIatilQWjIKLTBkrBbegI_NYb1w7MqgsXMVk4oKKHw5dZseO3jSKoGcar867LfFFUFVPQU49wwilKnyU3ZMXhOPuAHQ1GV6gKh-0vHS31uiOilGxx6tOyUCc3GQ28usOTM5s0sa8N-GkxD4y7gbXwUdytX5UW70f2mC9Ax6QgaNI1_oeNFqem1w7TwEKz9bAHx',
        transcript: 'Fast-paced traversal of vibrant neon-lit street. High dynamic range capture highlights reflection in puddles.',
        tags: ['#cyberpunk', '#vlog', '#neon', '#street'],
        status: 'Synced',
        captions: {
          formal: 'FPV motion shot through a brightly illuminated neon commercial strip.',
          sarcastic: 'Walking past shiny glowing advertisements in the rain. Ultimate futuristic vibe.',
          humorousTech: 'Kinetic light trajectory rendering in highly reflective asphalt water deposits.',
          humorousNonTech: 'Dodging puddles while walking past a massive wall of flashy video billboards.',
          audio: 'Transcribed audio text.', none: '', selectedTone: 'formal',
        }
      }
    ]
  }
];

export const MOCK_SEARCH_RESULTS = [
  {
    fileName: 'Expedition_Raw_02.mp4',
    timeLabel: '00:12:45',
    seconds: 765,
    text: 'The subject is seen traversing the rocky terrain. They are wearing a blue jacket and heavy-duty hiking boots. Weather conditions appear overcast with slight wind.',
    type: 'SCENE MATCH',
    confidence: 'high'
  },
  {
    fileName: 'Basecamp_Setup_v1.mov',
    timeLabel: '01:04:12',
    seconds: 3852,
    text: 'Preparing gear near the tent. Subject removes their blue jacket and places it on the camp chair. Focus shifts to the equipment bag.',
    type: 'SCENE MATCH',
    confidence: 'medium'
  },
  {
    fileName: 'Expedition_Raw_02.mp4',
    timeLabel: '00:15:30',
    seconds: 930,
    text: 'Close up on the footwear navigating loose gravel. The hiking boots provide stability. The bottom hem of the blue jacket is visible in the upper frame.',
    type: 'SCENE MATCH',
    confidence: 'high'
  }
];

export const MOCK_CHAT_HISTORY = [
  {
    id: 'chat-1',
    sender: 'user',
    text: 'Find all scenes with water.',
    timestamp: '10:42 AM'
  },
  {
    id: 'chat-2',
    sender: 'ai',
    text: 'Found 14 instances of water bodies across 3 projects. The longest continuous segment is in River_Crossing.mp4 (00:04:20 - 00:08:15).',
    timestamp: '10:42 AM'
  }
];
