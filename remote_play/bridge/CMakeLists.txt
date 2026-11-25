cmake_minimum_required(VERSION 3.24)

project(ps_live_media_bridge_check LANGUAGES CXX)

include(FetchContent)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Keep the upstream build focused on the local Remote Play media core.
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(LIBCHIAKING_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LIBCHIAKING_KAKUSAN OFF CACHE BOOL "" FORCE)
set(LIBCHIAKING_CLOUD OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
  chiaki_ng_core
  GIT_REPOSITORY https://github.com/chiaki-ng/chiaki-ng-core.git
  GIT_TAG 083f6e36deda83396e443ed48387844d660bcaee
  GIT_SHALLOW FALSE
)

FetchContent_MakeAvailable(chiaki_ng_core)

# Generate a tiny translation unit in the build directory. This checks that
# PS-LIVE's adapter header matches the pinned upstream MediaSink API without
# changing or generating source files in the repository.
set(bridge_check_source "${CMAKE_CURRENT_BINARY_DIR}/media_bridge_compile_check.cpp")
file(WRITE "${bridge_check_source}" [=[
#include "media_bridge.hpp"
#include <type_traits>

static_assert(std::is_base_of_v<
    libchiaking::media::MediaSink,
    ps_live::remote_play::MediaBridge>);

int main() { return 0; }
]=])

add_executable(media_bridge_compile_check EXCLUDE_FROM_ALL
  "${bridge_check_source}"
)
target_include_directories(media_bridge_compile_check PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}"
)
target_link_libraries(media_bridge_compile_check PRIVATE libchiaking)
target_compile_features(media_bridge_compile_check PRIVATE cxx_std_23)
