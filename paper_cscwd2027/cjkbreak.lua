-- Insert font switches and break points for Han / CJK punctuation.
local function is_han(c)
  return (c >= 0x4E00 and c <= 0x9FFF)
      or (c >= 0x3400 and c <= 0x4DBF)
      or (c >= 0xF900 and c <= 0xFAFF)
end

local function is_close(c)
  return c == 0x3001 or c == 0x3002 or c == 0xFF0C or c == 0xFF0E
      or c == 0xFF1A or c == 0xFF1B or c == 0xFF01 or c == 0xFF1F
      or c == 0xFF09 or c == 0x3009 or c == 0x300B or c == 0x300D
      or c == 0x300F or c == 0x3011
end

local function is_open(c)
  return c == 0xFF08 or c == 0x3008 or c == 0x300A or c == 0x300C
      or c == 0x300E or c == 0x3010
end

local function is_cjk_punct(c)
  return is_close(c) or is_open(c)
      or (c >= 0x3000 and c <= 0x303F)
      or (c >= 0xFF00 and c <= 0xFFEF)
end

local function break_cjk(s)
  if tex.count.cjkbreakoff > 0 then return s end
  local ok, result = pcall(function()
    if not utf8.len(s) then return s end
    local out = {}
    local in_cjk = false
    local prev_han = false
    local prev_close = false
    local function close_run()
      if in_cjk then
        out[#out + 1] = "}"
      end
      in_cjk = false
      prev_han = false
      prev_close = false
    end
    for _, c in utf8.codes(s) do
      local han = is_han(c)
      local punct = is_cjk_punct(c)
      if han or punct then
        if not in_cjk then
          out[#out + 1] = "{\\cjkfont "
          in_cjk = true
          prev_han = false
          prev_close = false
        end
        if han and (prev_han or prev_close) then
          out[#out + 1] = "\\cjkbr{}"
        elseif punct and is_open(c) and prev_han then
          out[#out + 1] = "\\cjkbr{}"
        end
        out[#out + 1] = utf8.char(c)
        prev_han = han
        prev_close = is_close(c)
      else
        close_run()
        out[#out + 1] = utf8.char(c)
      end
    end
    close_run()
    return table.concat(out)
  end)
  if ok then return result else return s end
end

luatexbase.add_to_callback("process_input_buffer", break_cjk, "cjk_line_break")
