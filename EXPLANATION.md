# Python Concurrency Explained: Asyncio and Multiprocessing

This document explains how this project combines **asyncio** (for I/O-bound operations) and **multiprocessing** (for CPU-bound operations) to efficiently handle concurrent tasks.

## Table of Contents
1. [Async and Await Keywords](#async-and-await-keywords)
2. [Asyncio.gather()](#asynciogather)
3. [Asyncio.get_running_loop() vs get_event_loop()](#asyncioget_running_loop-vs-get_event_loop)
4. [ProcessPoolExecutor](#processpoolexecutor)
5. [loop.run_in_executor()](#looprun_in_executor)
6. [add_done_callback()](#add_done_callback)
7. [How This Project Uses Concurrency](#how-this-project-uses-concurrency)

---

## Async and Await Keywords

### `async` Keyword

The `async` keyword is used to define an **asynchronous function** (also called a coroutine). An async function can be paused and resumed, allowing other code to run while it's waiting for I/O operations to complete.

```python
async def download_image(session, url, filename, pbar):
    # This function can pause and let other code run
    async with session.get(url) as response:
        content = await response.read()
```

**Key Points:**
- An `async def` function returns a **coroutine object**, not the actual result
- The function doesn't execute until it's awaited or scheduled on an event loop
- Async functions are designed for **I/O-bound operations** (network requests, file I/O, database queries)

### `await` Keyword

The `await` keyword pauses the execution of an async function until the awaited operation completes. While waiting, Python can run other async functions, making efficient use of time.

```python
content = await response.read()  # Pause here, let other tasks run
await f.write(content)           # Pause here too
```

**Key Points:**
- `await` can only be used inside `async` functions
- It yields control back to the event loop, allowing other coroutines to run
- It waits for the result without blocking the entire program
- This is the key to concurrent I/O operations

**Example in this project:**
```python
# Line 23: await response.read() - waits for HTTP response without blocking
# Line 25: await f.write(content) - waits for file write without blocking
# Line 90: await asyncio.gather(*tasks) - waits for all downloads to complete
```

---

## asyncio.gather()

`asyncio.gather()` is used to run multiple coroutines concurrently and wait for all of them to complete.

```python
download_files = await asyncio.gather(*tasks)
analysis_summaries = await asyncio.gather(*results)
```

**What it does:**
- Takes multiple coroutines/futures as arguments (using `*tasks` to unpack a list)
- Schedules all of them to run concurrently on the event loop
- Returns a list of results in the same order as the input
- If any coroutine raises an exception, `gather()` will raise it (unless `return_exceptions=True` is used)

**In this project:**
- **Line 90**: Gathers all download tasks to run concurrently - all images download at the same time
- **Line 115**: Gathers all image processing tasks to run concurrently

**Benefits:**
- Instead of downloading images one-by-one (which would take 10× longer), all 10 download simultaneously
- Much faster than sequential execution for I/O-bound operations

---

## asyncio.get_running_loop() vs get_event_loop()

### `asyncio.get_running_loop()`

```python
loop = asyncio.get_running_loop()  # Line 99
```

**What it does:**
- Returns the event loop that is **currently running** in the current thread
- Can only be called from within a coroutine or callback that's running on an event loop
- **Recommended approach** (Python 3.7+)

**Key Points:**
- Raises `RuntimeError` if no event loop is running
- This is the **safe** way to get the loop - it ensures you're getting the correct, active loop

### `asyncio.get_event_loop()`

**What it does:**
- Gets the event loop for the current thread
- If no loop exists, it creates a new one (in some Python versions)
- Can be called from anywhere, even outside async context

**Why get_running_loop() is preferred:**
- `get_event_loop()` can create a new loop if one doesn't exist, which can lead to unexpected behavior
- `get_running_loop()` ensures you're working with the actual running loop
- Better error handling - fails fast if called outside async context
- **Python 3.10+**: `get_event_loop()` raises RuntimeError in async context, pushing you toward `get_running_loop()`

**In this project (Line 99):**
```python
loop = asyncio.get_running_loop()
```
We use this to get the running loop so we can schedule CPU-bound tasks in a process pool while still being inside an async context.

---

## ProcessPoolExecutor

`ProcessPoolExecutor` is used to run CPU-bound tasks in separate processes, utilizing multiple CPU cores.

```python
with ProcessPoolExecutor() as pool:
    # Run CPU-intensive tasks in separate processes
```

**What it does:**
- Creates a pool of worker processes (by default, one per CPU core)
- Distributes tasks across these processes
- Each process runs in a separate Python interpreter
- Perfect for **CPU-bound operations** that benefit from true parallelism

**Key Points:**
- **Multiprocessing** (separate processes) vs **Multithreading** (same process, different threads)
- Processes don't share memory (unlike threads), which avoids Python's Global Interpreter Lock (GIL)
- Ideal for CPU-intensive tasks like image processing, mathematical computations, data parsing
- More overhead than threading (process creation, inter-process communication)

**In this project (Line 103):**
```python
with ProcessPoolExecutor() as pool:
```
We use it to process images with OpenCV across multiple CPU cores. Each image analysis runs in a separate process, so all CPU cores work simultaneously.

**Why not use ThreadPoolExecutor?**
- OpenCV/image processing is CPU-bound
- Python's GIL prevents true parallelism with threads for CPU-bound work
- Processes bypass the GIL, enabling true multi-core execution

---

## loop.run_in_executor()

`loop.run_in_executor()` allows you to run synchronous (blocking) functions in an executor (like ProcessPoolExecutor) without blocking the event loop.

```python
fut = loop.run_in_executor(pool, detect_stars_and_process, fname)
```

**What it does:**
- Schedules a blocking function to run in an executor (process pool or thread pool)
- Returns a `Future` object (a promise of a result)
- The event loop continues running other coroutines while the executor processes the task
- You can `await` the future to get the result

**Parameters:**
- `pool`: The executor (ProcessPoolExecutor or ThreadPoolExecutor)
- `detect_stars_and_process`: The function to run
- `fname`: Arguments to pass to the function

**Why it's needed:**
- `detect_stars_and_process()` is a regular (synchronous) function, not async
- We can't call it directly in async code without blocking the event loop
- `run_in_executor()` runs it in a separate process/thread, keeping the event loop responsive

**In this project (Line 109):**
```python
fut = loop.run_in_executor(pool, detect_stars_and_process, fname)
```
This runs the CPU-intensive image processing in a separate process while the event loop remains free to handle other tasks.

---

## add_done_callback()

`add_done_callback()` registers a function to be called when a Future completes (successfully or with an error).

```python
fut.add_done_callback(lambda _: pbar.update(1))
```

**What it does:**
- Adds a callback function that will be called when the Future finishes
- The callback receives the Future object as its argument
- Useful for side effects like updating progress bars, logging, cleanup

**In this project (Line 110):**
```python
fut.add_done_callback(lambda _: pbar.update(1))
```
Every time an image finishes processing, the progress bar updates by 1. This happens automatically without explicitly checking each future's status.

**Why use it:**
- Non-blocking way to handle completion
- Clean separation of concerns - the callback handles side effects
- Works well with progress bars, logging, notifications

**Alternative approach (without callback):**
```python
# Less elegant - would need to check each future individually
for future in results:
    await future
    pbar.update(1)
```

---

## How This Project Uses Concurrency

This project demonstrates a **hybrid approach** combining asyncio and multiprocessing:

### Phase 1: Asynchronous Downloads (I/O-bound)
```python
# Lines 85-90
tasks = []
for item in valid_items:
    tasks.append(download_image(session, url, f"space_{i}.jpg", download_pbar))
download_files = await asyncio.gather(*tasks)
```

**Why asyncio?**
- Downloading images is I/O-bound (waiting for network responses)
- Asyncio allows hundreds of downloads to happen concurrently
- Uses minimal resources (single thread, event loop)
- Much faster than sequential downloads

### Phase 2: Multiprocessing for Image Analysis (CPU-bound)
```python
# Lines 103-115
with ProcessPoolExecutor() as pool:
    for fname in downloaded_files:
        fut = loop.run_in_executor(pool, detect_stars_and_process, fname)
        fut.add_done_callback(lambda _: pbar.update(1))
        results.append(fut)
    analysis_summaries = await asyncio.gather(*results)
```

**Why multiprocessing?**
- Image processing with OpenCV is CPU-bound
- Requires true parallelism (multiple CPU cores)
- ProcessPoolExecutor bypasses Python's GIL
- Each image processes on a different CPU core simultaneously

### The Best of Both Worlds

This pattern is common in real-world applications:
- **Asyncio** for I/O operations (APIs, databases, file I/O)
- **Multiprocessing** for CPU-intensive work (image/video processing, scientific computations)
- Both coordinated through the same event loop using `run_in_executor()`

### Performance Benefits

**Sequential approach:**
- Download 10 images: 10 × 2 seconds = 20 seconds
- Process 10 images: 10 × 1 second = 10 seconds
- **Total: 30 seconds**

**Concurrent approach (this project):**
- Download 10 images: ~2 seconds (all concurrent)
- Process 10 images: ~2 seconds (4 cores, so ~3 batches)
- **Total: ~4 seconds**

That's roughly **7.5× faster**! 🚀

---

## Summary

| Concept | Purpose | Used For |
|---------|---------|----------|
| `async/await` | Non-blocking I/O operations | Network requests, file I/O |
| `asyncio.gather()` | Run multiple coroutines concurrently | Downloading multiple files at once |
| `get_running_loop()` | Get the active event loop safely | Accessing loop from within async context |
| `ProcessPoolExecutor` | True parallelism for CPU-bound tasks | Image processing, computations |
| `run_in_executor()` | Run blocking code without blocking event loop | Bridge between async and sync code |
| `add_done_callback()` | Handle completion events | Progress bars, logging, cleanup |

This project showcases how to leverage Python's concurrency tools effectively by using the right tool for the right job: **asyncio for I/O, multiprocessing for CPU**.

