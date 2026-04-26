#ifndef PARAM_HPP_INCLUDED
#define PARAM_HPP_INCLUDED
typedef unsigned int uint;
typedef struct {
  const uint id;
  const char *name;
  const char *symbol;
  const float range_min;
  const float range_max;
  const char *unit;
} Param;
#endif
