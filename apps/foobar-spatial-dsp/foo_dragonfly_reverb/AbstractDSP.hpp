#ifndef ABSTRACT_DSP_HPP_INCLUDED
#define ABSTRACT_DSP_HPP_INCLUDED
#include <cstdint>
class AbstractDSP {
public:
  virtual void setParameterValue(uint32_t index, float value) = 0;
  virtual void run(const float** inputs, float** outputs, uint32_t frames) = 0;
  virtual void mute() = 0;
  virtual ~AbstractDSP() {}
};
#endif
