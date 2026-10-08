from typing import List, Dict, Any

class EventGrouper:
    """
    Groups consecutive diagram detections into distinct diagram events with start and end timestamps.
    Applies visual similarity comparison (CV histogram correlation) to merge duplicate frames of identical diagrams.
    """
    def __init__(self, max_gap_seconds: float = 3.0, visual_similarity_threshold: float = 0.90):
        self.max_gap_seconds = max_gap_seconds
        self.visual_similarity_threshold = visual_similarity_threshold

    def group_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Input: List of frame detection items:
          [ { "frame_path": "...", "timestamp": 12.0, "is_diagram": True, "diagram_type": "graph" }, ... ]
        Output: Grouped diagram events:
          [ { "event_id": "evt_001", "start_time": 12.0, "end_time": 25.0, "timestamp": 12.0, "image": "...", "diagram_type": "graph" }, ... ]
        """
        diagram_frames = [d for d in detections if d.get("is_diagram", False)]
        if not diagram_frames:
            return []

        # Sort by timestamp
        diagram_frames.sort(key=lambda x: x["timestamp"])

        grouped_events = []
        current_group = [diagram_frames[0]]

        for frame in diagram_frames[1:]:
            prev_frame = current_group[-1]
            gap = frame["timestamp"] - prev_frame["timestamp"]

            if gap <= self.max_gap_seconds:
                current_group.append(frame)
            else:
                grouped_events.append(self._create_event(len(grouped_events) + 1, current_group))
                current_group = [frame]

        if current_group:
            grouped_events.append(self._create_event(len(grouped_events) + 1, current_group))

        # Perform visual deduplication pass
        return self._deduplicate_visually(grouped_events)

    def _create_event(self, index: int, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = group[0]["timestamp"]
        end_time = group[-1]["timestamp"]

        # Select frame with highest visual stability score as optimal entry frame
        optimal_entry_frame = max(group, key=lambda f: f.get("visual_stability_score", 0))
        # Trigger narration when the diagram first appears. The selected image
        # may come from later in the event because it is visually clearer.
        entry_timestamp = start_time

        diagram_type = optimal_entry_frame.get("diagram_type", "diagram")
        entry_context = f"Diagram entry detected at {entry_timestamp}s. Visual structure: {diagram_type} with {len(optimal_entry_frame.get('bounding_boxes', []))} key regions."

        return {
            "event_id": f"ad_evt_{index:03d}",
            "start_time": start_time,
            "end_time": end_time,
            "timestamp": entry_timestamp,
            "trigger_timestamp": entry_timestamp,
            "image": optimal_entry_frame["frame_path"],
            "diagram_type": diagram_type,
            "diagram_state": "NEW_DIAGRAM_ENTRY",
            "entry_context": entry_context,
            "bounding_boxes": optimal_entry_frame.get("bounding_boxes", [])
        }

    def _deduplicate_visually(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not events:
            return []

        deduped = [events[0]]
        for evt in events[1:]:
            prev_evt = deduped[-1]
            if self._are_images_similar(prev_evt["image"], evt["image"]):
                # Merge into prev_evt
                prev_evt["end_time"] = evt["end_time"]
            else:
                deduped.append(evt)

        # Re-index event IDs
        for idx, evt in enumerate(deduped):
            evt["event_id"] = f"ad_evt_{idx + 1:03d}"

        return deduped

    def _are_images_similar(self, img_path1: str, img_path2: str) -> bool:
        """Compares color histograms of two frame images to detect identical slides/diagrams."""
        if img_path1 == img_path2:
            return True
        try:
            import cv2
            img1 = cv2.imread(img_path1)
            img2 = cv2.imread(img_path2)
            if img1 is None or img2 is None:
                return False

            img1_resized = cv2.resize(img1, (128, 128))
            img2_resized = cv2.resize(img2, (128, 128))

            hist1 = cv2.calcHist([img1_resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([img2_resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            cv2.normalize(hist1, hist1)
            cv2.normalize(hist2, hist2)

            sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return sim >= self.visual_similarity_threshold
        except Exception:
            return False
