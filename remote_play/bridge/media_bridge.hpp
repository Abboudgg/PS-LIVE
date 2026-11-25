#pragma once

// PS-LIVE adapter boundary for chiaki-ng-core.
// This is an interface scaffold; it does not start or own a Remote Play session.

#include <libchiaking/detail/media/media_sink.hpp>

#include <string_view>

namespace ps_live::remote_play {

// Implementations must enqueue/copy callback data quickly. chiaki-ng-core says
// callback units are valid only for the duration of each callback.
class MediaOutput {
 public:
  virtual ~MediaOutput() = default;

  virtual void on_stream_description(
      const libchiaking::media::StreamDescription& description) = 0;

  // Return false when the bounded video queue cannot accept this frame.
  // The implementation must copy the frame bytes and any profile header
  // before returning.
  virtual auto enqueue_video(const libchiaking::media::VideoUnit& unit)
      -> bool = 0;

  // Return false when the audio queue cannot accept this unit. Copy its bytes
  // and format metadata before returning.
  virtual auto enqueue_audio(const libchiaking::media::AudioUnit& unit)
      -> bool = 0;

  virtual void on_video_gap() = 0;

  virtual void on_feedback(
      const libchiaking::controllers::ControllerFeedback& feedback) = 0;
};

// Adapts chiaki-ng-core callbacks to a PS-LIVE-owned media queue.
// The referenced MediaOutput must outlive this bridge and its Remote Play
// session. Methods are called by the session thread and must remain fast.
class MediaBridge final : public libchiaking::media::MediaSink {
 public:
  explicit MediaBridge(MediaOutput& output) noexcept : output_(output) {}

  void on_stream_description(
      const libchiaking::media::StreamDescription& description) override {
    output_.on_stream_description(description);
  }

  auto on_video(const libchiaking::media::VideoUnit& unit)
      -> libchiaking::media::VideoResult override {
    using libchiaking::media::VideoResult;
    using libchiaking::media::VideoVerdict;

    return output_.enqueue_video(unit)
               ? VideoResult{VideoVerdict::accepted, 0}
               : VideoResult{VideoVerdict::dropped, 0};
  }

  void on_video_gap() override { output_.on_video_gap(); }

  auto on_audio(const libchiaking::media::AudioUnit& unit)
      -> libchiaking::media::AudioResult override {
    using libchiaking::media::AudioResult;
    using libchiaking::media::AudioVerdict;

    return output_.enqueue_audio(unit)
               ? AudioResult{AudioVerdict::accepted, 0}
               : AudioResult{AudioVerdict::failed, 0};
  }

  void on_feedback(
      const libchiaking::controllers::ControllerFeedback& feedback) override {
    output_.on_feedback(feedback);
  }

  auto decoder_name() const -> std::string_view override {
    return "PS-LIVE media bridge";
  }

 private:
  MediaOutput& output_;
};

}  // namespace ps_live::remote_play
