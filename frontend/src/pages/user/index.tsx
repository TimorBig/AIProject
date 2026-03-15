/**
 * 用户页面
 */
import { View, Text, Button } from '@tarojs/components'
import { useState } from 'react'
import Taro from '@tarojs/taro'
import './index.scss'

function User() {
  const [userInfo, setUserInfo] = useState({
    name: '未登录',
    avatar: ''
  })

  const handleLogin = () => {
    // 模拟登录
    Taro.showLoading({ title: '登录中...' })
    setTimeout(() => {
      setUserInfo({
        name: '测试用户',
        avatar: ''
      })
      Taro.hideLoading()
      Taro.showToast({ title: '登录成功', icon: 'success' })
    }, 1000)
  }

  return (
    <View className='user-page'>
      <View className='user-page__header'>
        <View className='user-page__avatar'>
          <Text>{userInfo.name.charAt(0)}</Text>
        </View>
        <Text className='user-page__name'>{userInfo.name}</Text>
      </View>
      <View className='user-page__content'>
        <View className='user-page__menu'>
          <View className='user-page__menu-item'>
            <Text>我的订单</Text>
          </View>
          <View className='user-page__menu-item'>
            <Text>我的收藏</Text>
          </View>
          <View className='user-page__menu-item'>
            <Text>设置</Text>
          </View>
        </View>
        <Button className='user-page__btn' onClick={handleLogin}>
          登录
        </Button>
      </View>
    </View>
  )
}

export default User
