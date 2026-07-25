/**
 * Scheduler Module
 * Handles scheduling of trading tasks and intervals
 */

class Scheduler {
  constructor(config) {
    this.config = config;
    this.tasks = [];
    this.intervals = [];
    this.timeouts = [];
    this.isRunning = false;
    this.taskId = 0;
  }

  /**
   * Schedule a recurring task
   * @param {Function} task - Task function to execute
   * @param {number} intervalMs - Interval in milliseconds
   * @param {string} name - Task name
   * @returns {number} Task ID
   */
  schedule(task, intervalMs, name = 'unnamed') {
    const id = ++this.taskId;
    
    const taskObj = {
      id,
      name,
      task,
      intervalMs,
      lastRun: 0,
      nextRun: Date.now() + intervalMs,
      count: 0,
      errors: 0
    };
    
    this.tasks.push(taskObj);
    
    // Start the interval
    const interval = setInterval(async () => {
      if (!this.isRunning) return;
      
      const now = Date.now();
      if (now >= taskObj.nextRun) {
        await this.executeTask(taskObj);
        taskObj.lastRun = now;
        taskObj.nextRun = now + intervalMs;
        taskObj.count++;
      }
    }, Math.min(intervalMs, 1000)); // Check every second or interval
    
    this.intervals.push(interval);
    
    console.log(`⏰ Scheduled task "${name}" (ID: ${id}) every ${intervalMs / 1000}s`);
    
    return id;
  }

  /**
   * Execute a single task
   * @param {object} taskObj - Task object
   */
  async executeTask(taskObj) {
    try {
      const startTime = Date.now();
      await taskObj.task();
      const duration = Date.now() - startTime;
      
      if (duration > 1000) {
        console.log(`⏱️ Task "${taskObj.name}" took ${duration}ms`);
      }
    } catch (error) {
      taskObj.errors++;
      console.error(`❌ Task "${taskObj.name}" error:`, error.message);
      
      // Stop the task if it fails too many times
      if (taskObj.errors >= 5) {
        console.error(`⚠️ Task "${taskObj.name}" failed 5 times. Stopping.`);
        this.cancel(taskObj.id);
      }
    }
  }

  /**
   * Schedule a one-time task
   * @param {Function} task - Task function to execute
   * @param {number} delayMs - Delay in milliseconds
   * @param {string} name - Task name
   * @returns {number} Timeout ID
   */
  scheduleOnce(task, delayMs, name = 'unnamed') {
    const id = setTimeout(async () => {
      try {
        console.log(`⏰ Executing one-time task "${name}"`);
        await task();
      } catch (error) {
        console.error(`❌ One-time task "${name}" error:`, error.message);
      }
    }, delayMs);
    
    this.timeouts.push(id);
    console.log(`⏰ Scheduled one-time task "${name}" in ${delayMs / 1000}s`);
    
    return id;
  }

  /**
   * Cancel a scheduled task
   * @param {number} taskId - Task ID to cancel
   * @returns {boolean} Success
   */
  cancel(taskId) {
    const index = this.tasks.findIndex(t => t.id === taskId);
    if (index === -1) {
      return false;
    }
    
    // Clear the interval
    if (this.intervals[index]) {
      clearInterval(this.intervals[index]);
      this.intervals.splice(index, 1);
    }
    
    this.tasks.splice(index, 1);
    console.log(`❌ Task ${taskId} cancelled`);
    return true;
  }

  /**
   * Cancel all tasks
   */
  cancelAll() {
    // Clear all intervals
    for (const interval of this.intervals) {
      clearInterval(interval);
    }
    this.intervals = [];
    
    // Clear all timeouts
    for (const timeout of this.timeouts) {
      clearTimeout(timeout);
    }
    this.timeouts = [];
    
    this.tasks = [];
    console.log('🔄 All tasks cancelled');
  }

  /**
   * Stop all scheduled tasks
   */
  stop() {
    this.isRunning = false;
    this.cancelAll();
  }

  /**
   * Start the scheduler
   */
  start() {
    this.isRunning = true;
    console.log('▶️ Scheduler started');
  }

  /**
   * Get all scheduled tasks
   * @returns {object[]} List of tasks
   */
  getTasks() {
    return this.tasks.map(t => ({
      id: t.id,
      name: t.name,
      intervalMs: t.intervalMs,
      lastRun: t.lastRun,
      nextRun: t.nextRun,
      count: t.count,
      errors: t.errors,
      status: this.isRunning ? 'running' : 'stopped'
    }));
  }

  /**
   * Get task status
   * @param {number} taskId - Task ID
   * @returns {object|null} Task status
   */
  getTaskStatus(taskId) {
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) return null;
    
    return {
      id: task.id,
      name: task.name,
      intervalMs: task.intervalMs,
      lastRun: task.lastRun,
      nextRun: task.nextRun,
      count: task.count,
      errors: task.errors,
      timeUntilNext: task.nextRun - Date.now()
    };
  }

  /**
   * Pause a specific task
   * @param {number} taskId - Task ID
   * @returns {boolean} Success
   */
  pause(taskId) {
    const index = this.tasks.findIndex(t => t.id === taskId);
    if (index === -1) {
      return false;
    }
    
    // Clear the interval but keep the task
    if (this.intervals[index]) {
      clearInterval(this.intervals[index]);
      this.intervals[index] = null;
    }
    
    console.log(`⏸️ Task ${taskId} paused`);
    return true;
  }

  /**
   * Resume a paused task
   * @param {number} taskId - Task ID
   * @returns {boolean} Success
   */
  resume(taskId) {
    const index = this.tasks.findIndex(t => t.id === taskId);
    if (index === -1) {
      return false;
    }
    
    const task = this.tasks[index];
    
    // Restart the interval
    const interval = setInterval(async () => {
      if (!this.isRunning) return;
      
      const now = Date.now();
      if (now >= task.nextRun) {
        await this.executeTask(task);
        task.lastRun = now;
        task.nextRun = now + task.intervalMs;
        task.count++;
      }
    }, Math.min(task.intervalMs, 1000));
    
    this.intervals[index] = interval;
    
    console.log(`▶️ Task ${taskId} resumed`);
    return true;
  }

  /**
   * Run a task immediately (schedule on demand)
   * @param {number} taskId - Task ID
   * @returns {boolean} Success
   */
  runNow(taskId) {
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) {
      return false;
    }
    
    // Execute asynchronously
    this.executeTask(task);
    task.lastRun = Date.now();
    task.nextRun = task.lastRun + task.intervalMs;
    task.count++;
    
    console.log(`▶️ Task ${taskId} executed immediately`);
    return true;
  }

  /**
   * Get scheduler status
   * @returns {object} Scheduler status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      activeTasks: this.tasks.length,
      activeIntervals: this.intervals.filter(i => i !== null).length,
      pendingTimeouts: this.timeouts.length,
      tasks: this.getTasks()
    };
  }

  /**
   * Schedule a task to run at a specific time
   * @param {Function} task - Task function
   * @param {Date} time - Time to execute
   * @param {string} name - Task name
   * @returns {number} Task ID
   */
  scheduleAt(task, time, name = 'scheduled_at') {
    const delay = time.getTime() - Date.now();
    if (delay <= 0) {
      console.log(`⚠️ Scheduled time ${time.toISOString()} is in the past`);
      return this.scheduleOnce(task, 0, name);
    }
    
    return this.scheduleOnce(task, delay, name);
  }

  /**
   * Schedule a daily task at a specific time
   * @param {Function} task - Task function
   * @param {string} timeStr - Time in format 'HH:MM' (24-hour)
   * @param {string} name - Task name
   * @returns {number} Task ID
   */
  scheduleDaily(task, timeStr, name = 'daily_task') {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const now = new Date();
    const scheduled = new Date(now);
    scheduled.setHours(hours, minutes, 0, 0);
    
    // If scheduled time is in the past, schedule for tomorrow
    if (scheduled <= now) {
      scheduled.setDate(scheduled.getDate() + 1);
    }
    
    const delay = scheduled.getTime() - now.getTime();
    
    // Schedule the first run
    const id = this.scheduleOnce(task, delay, `${name} (first run)`);
    
    // Schedule it to run daily
    const dailyMs = 24 * 60 * 60 * 1000;
    const dailyId = this.schedule(task, dailyMs, `${name} (daily)`);
    
    console.log(`📅 Daily task "${name}" scheduled at ${timeStr}`);
    
    return dailyId;
  }

  /**
   * Schedule a task with exponential backoff retry
   * @param {Function} task - Task function
   * @param {number} baseDelay - Base delay in milliseconds
   * @param {number} maxRetries - Maximum retries
   * @param {string} name - Task name
   * @returns {number} Task ID
   */
  scheduleWithBackoff(task, baseDelay, maxRetries = 3, name = 'backoff_task') {
    let retries = 0;
    let delay = baseDelay;
    
    const executeWithBackoff = async () => {
      try {
        await task();
        retries = 0;
        delay = baseDelay;
        return true;
      } catch (error) {
        retries++;
        if (retries >= maxRetries) {
          console.error(`❌ Task "${name}" failed after ${maxRetries} retries`);
          return false;
        }
        
        // Exponential backoff
        delay = delay * 2;
        console.log(`⚠️ Task "${name}" failed. Retry ${retries}/${maxRetries} in ${delay}ms`);
        
        // Reschedule with increased delay
        setTimeout(executeWithBackoff, delay);
        return false;
      }
    };
    
    return this.scheduleOnce(executeWithBackoff, 0, name);
  }
}

module.exports = { Scheduler };
