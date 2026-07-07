const config = {
  env: process.env.NODE_ENV || 'development',
  logLevel: process.env.LOG_LEVEL || 'info',
  dbType: process.env.DB_TYPE || 'catalyst_datastore',
  aiProvider: process.env.AI_PROVIDER || 'catalyst_quickml',
  cacheType: process.env.CACHE_TYPE || 'catalyst_cache',
  convokraftBotId: process.env.CONVOKRAFT_BOT_ID || '',
  get isDev() {
    return this.env === 'development';
  },
  get isProd() {
    return this.env === 'production';
  },
};

export default config;
