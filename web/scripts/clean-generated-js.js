import { readdir, unlink } from 'fs/promises';
import { join } from 'path';

async function cleanGeneratedJsFiles(dir = './src') {
  try {
    const files = await readdir(dir, { withFileTypes: true });
    
    for (const file of files) {
      const fullPath = join(dir, file.name);
      
      if (file.isDirectory()) {
        // 递归清理子目录
        await cleanGeneratedJsFiles(fullPath);
      } else if (file.name.endsWith('.js') && !file.name.includes('node_modules')) {
        // 检查是否对应的.tsx或.ts文件也存在
        const tsxFile = fullPath.replace(/\.js$/, '.tsx');
        const tsFile = fullPath.replace(/\.js$/, '.ts');
        
        if (await fileExists(tsxFile) || await fileExists(tsFile)) {
          console.log(`删除残留的JS文件: ${fullPath}`);
          await unlink(fullPath);
        }
      }
    }
  } catch (error) {
    console.error('清理JS文件时出错:', error);
    process.exit(1);
  }
}

async function fileExists(filePath) {
  try {
    await import('fs').then(fs => fs.promises.access(filePath));
    return true;
  } catch {
    return false;
  }
}

cleanGeneratedJsFiles();