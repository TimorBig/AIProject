/**
 * 首页
 */
import { View, Text } from '@tarojs/components'
import { useEffect } from 'react'
import Taro from '@tarojs/taro'
import './index.scss'

function Index() {
  useEffect(() => {
    // 页面加载时执行
    console.log('Index page mounted')
  }, [])

  const handleNavigate = () => {
    Taro.navigateTo({
      url: '/pages/user/index'
    })
  }

  return (
    <View className='index-page'>
      <View className='index-page__header'>
        <Text className='index-page__title'>欢迎使用 Taro + Flask</Text>
        <Text className='index-page__subtitle'>全栈项目模板</Text>
      </View>
      <View className='index-page__content'>
        <View className='index-page__card' onClick={handleNavigate}>
          <Text>进入个人中心</Text>
        </View>
      </View>
    </View>
  )
}

export default Index
